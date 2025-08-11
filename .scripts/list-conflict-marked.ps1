[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
# Get all tracked files
$files = git ls-files
if (-not $files) { exit 0 }
# Find files containing each marker using git grep for better performance
$ours = git grep -l '<<<<<<<' | Sort-Object -Unique
$theirs = git grep -l '>>>>>>>' | Sort-Object -Unique
if (-not $ours -or -not $theirs) { exit 0 }
# Intersect
$set = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($p in $ours) { [void]$set.Add((Resolve-Path -LiteralPath $p).Path) }
$both = New-Object System.Collections.Generic.List[string]
foreach ($p in $theirs) {
    $rp = (Resolve-Path -LiteralPath $p).Path
    if ($set.Contains($rp)) { [void]$both.Add($rp) }
}
# Output relative paths
$root = (Get-Location).Path
$both | Sort-Object -Unique | ForEach-Object { $_.Replace($root + [IO.Path]::DirectorySeparatorChar, '') }
