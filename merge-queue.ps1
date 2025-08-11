<# 
.SYNOPSIS
  Queue-merges branches into a target with: auto-discovery, resume, dry-run, and auto-push.
  PowerShell port of merge-queue.sh
#>

[CmdletBinding()]
param(
    [string]$Target = "phone-chron",
    [string[]]$Pattern,                 # Add one or more discovery regexes (PowerShell/.NET regex)
    [string[]]$Branch,                  # Explicit branches (e.g., origin/feature-x)
    [switch]$DryRun,                    # Preview plan and exit
    [switch]$Force,                     # Auto-stash dirty tree
    [switch]$Reset,                     # Rebuild queue/reset index
    [switch]$NoPush,                    # Do NOT push after each merge
    [switch]$Help
)

if ($Help) {
    @"
Usage:
  .\merge-queue.ps1 [-Target phone-chron] [-Pattern '^origin/copilot/' -Pattern '^origin/fix-'] [-Branch origin/x ...] [-DryRun] [-Force] [-Reset] [-NoPush]

Examples:
  .\merge-queue.ps1
  .\merge-queue.ps1 -DryRun
  .\merge-queue.ps1 -Pattern '^origin/feature/' -Branch origin/fix-123
"@ | Write-Host
    exit 0
}

# -------------------- Defaults & State --------------------
$ErrorActionPreference = 'Stop'
$StateDir = ".merge_queue"
$StateFile = Join-Path $StateDir "state.json"
$LockFile = Join-Path $StateDir "lock"
$DefaultPatterns = @('^origin/copilot/', '^origin/fix-')
if (-not $Pattern -or $Pattern.Count -eq 0) { $Pattern = $DefaultPatterns }

# -------------------- Utils --------------------
function Write-Log { param([string]$Msg) Write-Host ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg) }
function Stop-Fatal { param([string]$Msg) Write-Error $Msg; exit 1 }

function Invoke-Git {
    param([Parameter(Mandatory)][string]$GitArgs, [switch]$NoThrow)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "git"
    $psi.Arguments = $GitArgs
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $out = $p.StandardOutput.ReadToEnd()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    if ($p.ExitCode -ne 0 -and -not $NoThrow) {
        if ($err) { Write-Error $err.Trim() }
        Stop-Fatal "git $GitArgs failed with exit code $($p.ExitCode)"
    }
    return [pscustomobject]@{ ExitCode = $p.ExitCode; StdOut = $out; StdErr = $err }
}

function Test-GitCleanTree {
    # Returns $true if working tree is clean
    $diff = Invoke-Git "diff --quiet" -NoThrow
    if ($diff.ExitCode -ne 0) { return $false }
    $cached = Invoke-Git "diff --cached --quiet" -NoThrow
    if ($cached.ExitCode -ne 0) { return $false }
    return $true
}

function Get-State {
    if (-not (Test-Path $StateFile)) { return $null }
    try {
        return Get-Content $StateFile -Raw | ConvertFrom-Json
    }
    catch { Stop-Fatal "Failed to parse state file: $StateFile" }
}

function Set-State {
    param([string]$TargetBranch, [string[]]$BranchList, [int]$Index)
    if (-not (Test-Path $StateDir)) { New-Item -ItemType Directory -Path $StateDir | Out-Null }
    $obj = [pscustomobject]@{
        target      = $TargetBranch
        created_at  = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        branch_list = $BranchList
        index       = $Index
    }
    $obj | ConvertTo-Json -Depth 5 | Set-Content -NoNewline $StateFile
}

function Update-StateIndex {
    param([int]$Index)
    $s = Get-State
    if (-not $s) { Stop-Fatal "State missing when updating index." }
    $s.index = $Index
    $s | ConvertTo-Json -Depth 5 | Set-Content -NoNewline $StateFile
}

# -------------------- Locking & Cleanup --------------------
$global:AUTO_STASHED = $false
if (-not (Test-Path $StateDir)) { New-Item -ItemType Directory -Path $StateDir | Out-Null }
if (Test-Path $LockFile) { Stop-Fatal "Another merge-queue instance appears to be running. Delete '$LockFile' if stale." }
New-Item -ItemType File -Path $LockFile | Out-Null

$cleanup = {
    if (Test-Path $LockFile) { Remove-Item $LockFile -Force -ErrorAction SilentlyContinue }
    if ($global:AUTO_STASHED) {
        Write-Log "Restoring auto stash..."
        Invoke-Git "stash pop" -NoThrow | Out-Null
    }
}
# Ensure cleanup runs even on Ctrl+C
$null = Register-EngineEvent PowerShell.Exiting -Action $cleanup | Out-Null

try {
    # -------------------- Sanity --------------------
    Invoke-Git "rev-parse --is-inside-work-tree" | Out-Null

    # -------------------- Fetch/Prune --------------------
    Write-Log "Fetching all remotes (with prune)..."
    Invoke-Git "fetch --all --prune --tags" | Out-Null

    # -------------------- Clean tree or auto-stash --------------------
    if (-not (Test-GitCleanTree)) {
        if ($Force) {
            Write-Log "Dirty tree detected. Stashing (forced)."
            Invoke-Git "stash push -u -m `"merge-queue auto-stash $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`"" | Out-Null
            $global:AUTO_STASHED = $true
        }
        else {
            Stop-Fatal "Working tree is not clean. Commit/stash or rerun with -Force."
        }
    }

    # -------------------- Checkout target & FF to origin if present --------------------
    Write-Log "Checking out target: $Target"
    Invoke-Git "checkout `"$Target`"" | Out-Null
    $hasOriginTarget = (Invoke-Git "rev-parse --verify origin/$Target" -NoThrow).ExitCode -eq 0
    if ($hasOriginTarget) {
        Write-Log "Fast-forwarding $Target to origin..."
        Invoke-Git "merge --ff-only origin/$Target" -NoThrow | Out-Null
    }

    # -------------------- Build or Load Queue --------------------
    function New-MergeQueue {
        Write-Log ("Building candidate list from patterns: {0}" -f ($Pattern -join ", "))
        $refs = (Invoke-Git "for-each-ref --format='%(refname:short)' refs/remotes").StdOut -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

        $candidates = New-Object System.Collections.Generic.List[string]
        foreach ($ref in $refs) {
            foreach ($rx in $Pattern) {
                if ($ref -match $rx) { $candidates.Add($ref); break }
            }
        }
        if ($Branch) {
            foreach ($b in $Branch) { $candidates.Add($b) }
        }

        # De-dup
        $uniq = $candidates | Select-Object -Unique

        # Filter: skip already merged into target
        $filtered = New-Object System.Collections.Generic.List[string]
        foreach ($ref in $uniq) {
            $mb = Invoke-Git "merge-base --is-ancestor `"$ref`" `"$Target`"" -NoThrow
            if ($mb.ExitCode -eq 0) {
                Write-Log "Already merged -> skipping: $ref"
                continue
            }
            $filtered.Add($ref)
        }

        # Deterministic order
        return ($filtered | Sort-Object)
    }

    function Get-ConflictedFiles {
        $out = Invoke-Git "diff --name-only --diff-filter=U" -NoThrow
        if ($out.ExitCode -ne 0) { return @() }
        return ($out.StdOut -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }

    function Resolve-ConflictsStackBoth {
        param([string]$FilePath)
        try {
            $content = Get-Content -LiteralPath $FilePath -Raw -ErrorAction Stop
        }
        catch { return $false }
        $lines = $content -split "\r?\n", -1
        $out = New-Object System.Collections.Generic.List[string]
        $state = 'normal'
        $ours = New-Object System.Collections.Generic.List[string]
        $theirs = New-Object System.Collections.Generic.List[string]
        $changed = $false
        foreach ($ln in $lines) {
            if ($state -eq 'normal') {
                if ($ln -like '<<<<<<<*') { $state = 'ours'; $ours.Clear(); $theirs.Clear(); $changed = $true; continue }
                $out.Add($ln)
            }
            elseif ($state -eq 'ours') {
                if ($ln -like '=======') { $state = 'theirs'; continue }
                $ours.Add($ln)
            }
            elseif ($state -eq 'theirs') {
                if ($ln -like '>>>>>>>*') {
                    # Stack OURS first, then THEIRS
                    foreach ($l in $ours) { $out.Add($l) }
                    # Separate with a blank line to make it obvious
                    if ($ours.Count -gt 0 -and $theirs.Count -gt 0) { $out.Add('') }
                    foreach ($l in $theirs) { $out.Add($l) }
                    $state = 'normal'
                    continue
                }
                $theirs.Add($ln)
            }
        }
        if ($state -ne 'normal') { return $false }
        if (-not $changed) { return $false }
        $nl = "`r`n"
        $newText = [string]::Join($nl, $out)
        try {
            Set-Content -LiteralPath $FilePath -Value $newText -Encoding utf8 -NoNewline
            return $true
        }
        catch { return $false }
    }

    function AutoResolve-And-CommitIfPossible {
        $files = Get-ConflictedFiles
        if (-not $files -or $files.Count -eq 0) { return $false }
        $any = $false
        foreach ($f in $files) {
            if (Resolve-ConflictsStackBoth -FilePath $f) { $any = $true }
        }
        # Re-check if conflicts remain
        $after = Get-ConflictedFiles
        if ($after.Count -eq 0) {
            Invoke-Git "add -A" | Out-Null
            Invoke-Git "commit --no-edit" | Out-Null
            return $true
        }
        return $false
    }

    $state = Get-State
    $needInit = $false
    if (-not $state) { $needInit = $true }
    elseif ($Reset) { $needInit = $true }
    elseif ($state.target -ne $Target) { $needInit = $true }

    if ($needInit) {
        $list = New-MergeQueue
        Set-State -TargetBranch $Target -BranchList $list -Index 0
        Write-Log "Queue initialized for target '$Target'."
        $state = Get-State
    }
    else {
        Write-Log "Resuming existing queue for target '$($state.target)'."
    }

    $branches = @()
    if ($state.branch_list) { $branches = @($state.branch_list) }
    $index = [int]$state.index
    $total = $branches.Count
    if ($total -eq 0) {
        Write-Log "No branches to merge. Up to date."
        exit 0
    }

    # -------------------- Dry-run --------------------
    if ($DryRun) {
        Write-Log ('DRY RUN — Target: {0}' -f $Target)
        Write-Log ('Plan ({0} total, starting at index {1}):' -f $total, $index)
        for ($i = $index; $i -lt $total; $i++) {
            '{0,3}. {1} -> {2}' -f ($i + 1), $branches[$i], $Target | Write-Host
        }
        exit 0
    }

    # -------------------- Execute merges with resume --------------------
    for ($i = $index; $i -lt $total; $i++) {
        $ref = $branches[$i]
        Write-Log ("Merging ({0}/{1}): {2} -> {3}" -f ($i + 1), $total, $ref, $Target)

        # Defensive: ensure target checked out & up-to-date before each merge
        Invoke-Git "checkout `"$Target`"" | Out-Null
        Invoke-Git "fetch --all --prune --tags" | Out-Null
        if ((Invoke-Git "rev-parse --verify origin/$Target" -NoThrow).ExitCode -eq 0) {
            Invoke-Git "merge --ff-only origin/$Target" -NoThrow | Out-Null
        }

        # Attempt merge
        $merge = Invoke-Git "merge --no-ff -m `"Automated merge: $ref into $Target`" `"$ref`"" -NoThrow
        if ($merge.ExitCode -ne 0) {
            Write-Log "Merge reported conflicts for $ref. Attempting auto-resolve (stack OURS then THEIRS)..."
            if (AutoResolve-And-CommitIfPossible) {
                Write-Log "Conflicts auto-resolved and committed for: $ref"
            }
            else {
                Write-Log "Auto-resolve failed or conflicts remain. Halting queue."
                Write-Host "Next steps:"
                Write-Host "  1) Resolve conflicts (both versions kept; stack OURS then THEIRS)"
                Write-Host "  2) git add -A"
                Write-Host "  3) git commit --no-edit   # finalize the merge"
                Write-Host "  4) (optional) git push origin $Target"
                Write-Host "  5) Resume queue: .\merge-queue.ps1 -Target $Target"
                Update-StateIndex -Index $i
                exit 2
            }
        }

        if (-not $NoPush) {
            Write-Log "Pushing $Target..."
            Invoke-Git "push origin `"$Target`"" | Out-Null
        }

        Update-StateIndex -Index ($i + 1)
        Write-Log "Merged successfully: $ref"
    }

    Write-Log "All merges completed for target '$Target'."
}
finally {
    & $cleanup
}
