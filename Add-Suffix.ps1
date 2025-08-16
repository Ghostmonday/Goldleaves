# Save as: Add-Suffix.ps1
param(
    [Parameter(Mandatory = $true)]
    [string]$Suffix,                 # e.g. "_v2" or "-backup"

    [switch]$Recurse,                # Include subfolders
    [switch]$Preview                 # Show what would change, no renames
)

# Grab files in the working directory (and subdirs if -Recurse)
$files = Get-ChildItem -File -Recurse:$Recurse -ErrorAction Stop

foreach ($f in $files) {
    # Build the new name: <BaseName><Suffix><Extension>
    $newName = '{0}{1}{2}' -f $f.BaseName, $Suffix, $f.Extension
    if ($newName -eq $f.Name) { continue }  # No-op if already matches

    # Handle collisions by adding (1), (2), ...
    $target = Join-Path $f.DirectoryName $newName
    if (Test-Path -LiteralPath $target) {
        $i = 1
        do {
            $candidate = '{0}{1}({2}){3}' -f $f.BaseName, $Suffix, $i, $f.Extension
            $target = Join-Path $f.DirectoryName $candidate
            $i++
        } while (Test-Path -LiteralPath $target)
        $newName = Split-Path $target -Leaf
    }

    if ($Preview) {
        Write-Host ("{0}  ->  {1}" -f $f.Name, $newName)
    }
    else {
        Rename-Item -LiteralPath $f.FullName -NewName $newName -ErrorAction Stop
    }
}
