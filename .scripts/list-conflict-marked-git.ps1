[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
# Use git grep anchored to line start to avoid matching literals in code; -I skips binaries
$ours   = git grep -l -I -E '^(<<<<<<<)( .*)?$' -- . 2>$null
$theirs = git grep -l -I -E '^>>>>>>>' -- . 2>$null
if (-not $ours -or -not $theirs) { Write-Output 'NONE'; exit 0 }
$set = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($p in $ours) { [void]$set.Add($p) }
$both = New-Object System.Collections.Generic.List[string]
foreach ($p in $theirs) { if ($set.Contains($p)) { [void]$both.Add($p) } }
$out = $both | Sort-Object -Unique
if (-not $out -or $out.Count -eq 0) { Write-Output 'NONE' } else { $out | ForEach-Object { $_ } }
