[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# Build a map of conflicted files and their stage SHAs using ls-files -u
$lsu = @(git ls-files -u)
if (-not $lsu -or $lsu.Count -eq 0) {
  Write-Host 'NO_CONFLICTS'
  exit 0
}

$byPath = @{}
foreach ($line in $lsu) {
  # Format: <mode> <sha> <stage>\t<path>
  if ($line -match '^(\d+)\s+([0-9a-f]{40})\s+(\d)\t(.+)$') {
    $sha = $Matches[2]
    $stage = [int]$Matches[3]
    $path = $Matches[4]
    if (-not $byPath.ContainsKey($path)) { $byPath[$path] = @{} }
    $byPath[$path][$stage] = $sha
  }
}

if ($byPath.Count -eq 0) { Write-Host 'NO_CONFLICTS'; exit 0 }

foreach ($f in $byPath.Keys) {
  try {
    $sha2 = $byPath[$f][2]
    $sha3 = $byPath[$f][3]

    if ($sha2 -and $sha3) {
      $ours = git show -- $sha2
      $theirs = git show -- $sha3
      $nl = [Environment]::NewLine
      $combined = $ours + $nl + $nl + $theirs
      $dir = Split-Path -Parent $f
      if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
      }
      $full = Resolve-Path -LiteralPath $f -ErrorAction SilentlyContinue
      if (-not $full) { $full = Join-Path (Get-Location) $f }
      [System.IO.File]::WriteAllText($full, $combined, [System.Text.UTF8Encoding]::new($false))
      Write-Verbose "STACKED BOTH -> $f"
    }
    elseif ($sha2) {
      git checkout --ours -- $f | Out-Null
      Write-Verbose "FALLBACK OURS -> $f"
    }
    elseif ($sha3) {
      git checkout --theirs -- $f | Out-Null
      Write-Verbose "FALLBACK THEIRS -> $f"
    }
    else {
      # Unknown state; choose ours defensively
      git checkout --ours -- $f | Out-Null
      Write-Verbose "FALLBACK OURS (no stages) -> $f"
    }

    git add -- $f | Out-Null
  } catch {
    Write-Host ("ERR on {0}: {1}" -f $f, $_.Exception.Message)
    throw
  }
}

git commit --no-edit
