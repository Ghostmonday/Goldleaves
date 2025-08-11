# Auto-merge conflicts by concatenating ours + theirs (safe version)
# Run from repo root during a merge conflict

# Check for merge conflicts
$conflicts = git diff --name-only --diff-filter=U

if (-not $conflicts) {
    Write-Host "✅ No unresolved merge conflicts found. Exiting." -ForegroundColor Green
    exit 0
}

Write-Host "⚠ Found $($conflicts.Count) conflicted file(s). Starting merge..." -ForegroundColor Yellow

foreach ($file in $conflicts) {
    Write-Host "Processing conflicted file: $file" -ForegroundColor Cyan

    # Temp paths
    $oursTemp   = "$file.ours.tmp"
    $theirsTemp = "$file.theirs.tmp"

    # Extract both versions (suppress errors if side missing)
    git show ":2:$file" 2>$null > $oursTemp
    git show ":3:$file" 2>$null > $theirsTemp

    # Concatenate: ours first, theirs second
    "# === OURS ==="     | Out-File $file -Encoding UTF8
    if (Test-Path $oursTemp)   { Get-Content $oursTemp   | Out-File $file -Encoding UTF8 -Append }
    "`n# === THEIRS ===" | Out-File $file -Encoding UTF8 -Append
    if (Test-Path $theirsTemp) { Get-Content $theirsTemp | Out-File $file -Encoding UTF8 -Append }

    # Remove temp files
    Remove-Item $oursTemp, $theirsTemp -Force -ErrorAction SilentlyContinue

    # Stage for commit
    git add $file
}

Write-Host "✅ All conflicts concatenated and staged. Run 'git commit' to finalize." -ForegroundColor Green
