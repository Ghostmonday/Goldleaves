[CmdletBinding()]
param(
  [string]$Target = 'phone-chron',
  [int]$MaxIterations = 50
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

for ($i = 1; $i -le $MaxIterations; $i++) {
  Write-Host ("[drive] Iteration {0}/{1}" -f $i, $MaxIterations)

  # If any conflicts remain from a prior halt, resolve them first
  $conf = @(git diff --name-only --diff-filter=U)
  if ($conf.Count -gt 0) {
    Write-Host ("[drive] Resolving {0} conflicted files (stack OURS then THEIRS)" -f $conf.Count)
    & "$PSScriptRoot/resolve-both.ps1"
  }

  # Resume/advance the queue
  & "$repoRoot/merge-queue.ps1" -Target $Target -Force -NoPush
  $exit = $LASTEXITCODE
  Write-Host ("[drive] Queue exit code: {0}" -f $exit)

  if ($exit -eq 0) {
    Write-Host "[drive] Queue completed successfully."
    break
  } else {
    # On conflict, the queue halts with non-zero; loop will resolve and continue
    Start-Sleep -Milliseconds 200
  }
}
