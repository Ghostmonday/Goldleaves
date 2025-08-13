# PowerShell script to collect priority files for technical assessment
$sourceDir = "c:\Projects\Goldleaves_Final"
$targetDir = "c:\Projects\Goldleaves_Final\extracted_files\priority_assessment"

# Priority files list
$priorityFiles = @(
    # Models (most critical)
    "models\user.py",
    "models\client.py",
    "models\case.py",
    "models\organization.py",
    "models\contract.py",
    "models\agent.py",
    "models\base.py",
    "models\auth_router.py",

    # Service Layer
    "services\auth_service.py",
    "services\user_service.py",
    "services\agent.py",
    "services\config.py",
    "services\schemas.py",
    "services\token_service.py",

    # Router Implementations
    "routers\auth.py",
    "routers\client.py",
    "routers\case.py",
    "routers\agent.py",
    "routers\contract.py",
    "routers\main.py",

    # Package Configuration
    "requirements.txt",
    "pyproject.toml",
    ".env.example",
    "package.json",
    "alembic.ini",

    # Additional core business files
    "core\config.py",
    "core\database.py",
    "core\security.py",
    "core\dependencies.py",
    "schemas\agent.py",
    "schemas\core_contracts.py"
)

# Create target directory
if (!(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force
}

Write-Host "🎯 Collecting PRIORITY files for technical assessment..."
Write-Host ""

$foundCount = 0
$notFoundCount = 0

foreach ($file in $priorityFiles) {
    $sourcePath = Join-Path $sourceDir $file

    if (Test-Path $sourcePath) {
        # Create flattened filename
        $flattenedName = $file -replace "\\", "_"
        $targetPath = Join-Path $targetDir $flattenedName

        Copy-Item $sourcePath $targetPath -Force
        Write-Host "✅ CRITICAL: $file -> $flattenedName"
        $foundCount++
    } else {
        Write-Host "❌ Missing: $file"
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "📊 SUMMARY:"
Write-Host "✅ Found: $foundCount files"
Write-Host "❌ Missing: $notFoundCount files"
Write-Host "📁 Location: $targetDir"
Write-Host ""
Write-Host "🚀 Ready for technical assessment!"
