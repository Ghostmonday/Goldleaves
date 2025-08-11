$ErrorActionPreference = 'Stop'
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path ..

# 3) Local branches with upstreams and active branch
"SECTION:LOCAL_BRANCHES"
& git branch --format="%(refname:short) | local | -> %(upstream:short)"
"ACTIVE | $(& git rev-parse --abbrev-ref HEAD)"

# 4) Remote branches under origin/copilot/fix-* sorted oldest->newest with metadata
"SECTION:REMOTE_FIXES"
& git for-each-ref --sort=committerdate --format="%(refname:short)|%(committerdate:iso8601)|%(authorname)|%(subject)" refs/remotes/origin/copilot/fix-*

# 5) Confirm target branch
$target = 'phone-chron'
$localExists = $false
try { & git show-ref --verify --quiet "refs/heads/$target"; if ($LASTEXITCODE -eq 0) { $localExists = $true } } catch {}
$upstream = ''
try { $upstream = & git rev-parse --abbrev-ref "${target}@{upstream}" 2>$null } catch {}
"SECTION:TARGET"
if ($localExists) { Write-Output "local:yes" } else { Write-Output "local:no" }
if ($upstream -and $upstream.Trim() -ne '') { Write-Output ("tracking:" + $upstream.Trim()) } else { Write-Output "tracking:none" }

# 6) Compute merge queue: origin/copilot/fix-* not yet merged into phone-chron, sorted oldest->newest
"SECTION:MERGE_QUEUE"
$branches = @(& git for-each-ref --sort=committerdate --format="%(refname:short)" refs/remotes/origin/copilot/fix-*)
$queue = @()
foreach ($b in $branches) {
    & git merge-base --is-ancestor $b $target | Out-Null
    if ($LASTEXITCODE -ne 0) { $queue += $b }
}
$idx = 1
foreach ($b in $queue) {
    $meta = & git log -1 --format="%ci|%an|%s|%H" $b
    if ($meta) { "$idx|$b|$meta"; $idx++ }
}
"SECTION:END"
