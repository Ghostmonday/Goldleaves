# Phase 11 Dependencies Copy Script
# Copies the 20 most critical files for Phase 11 Frontend API Integration & Sync Layer
# Creates a flattened structure with all files at top level for easy review

$sourceRoot = "c:\Projects\Goldleaves_Final"
$destinationFolder = "c:\Projects\Goldleaves_Final\phase11_dependencies"

# The 20 most important files for Phase 11 (in order of importance)
$criticalFiles = @(
    # 1. Core RBAC Service (Essential permission checking logic)
    "services\rbac_service.py",
    
    # 2-4. Core Authentication & Security Infrastructure
    "core\security.py",
    "core\dependencies.py", 
    "models\auth_router.py",
    
    # 5-7. RBAC & Permission Management
    "schemas\auth\permissions.py",
    "schemas\security\permissions.py",
    "schemas\security\api_keys.py",
    
    # 8-10. Middleware & Request Processing (Critical for Frontend APIs)
    "routers\middleware.py",
    "routers\rate_limiter.py",
    "routers\main.py",
    
    # 11-13. User & Session Management
    "models\user.py",
    "models\user_schemas.py",
    "services\token_service.py",
    
    # 14-16. Base Schema Patterns (Templates for new frontend schemas)
    "schemas\base\responses.py",
    "schemas\base\pagination.py",
    "schemas\base\errors.py",
    
    # 17-19. Database & Configuration Foundation
    "core\db\session.py",
    "core\config.py",
    "core\exceptions.py",
    
    # 20. Document Services (For frontend document endpoints)
    "models\contract.py"
)

Write-Host "Phase 11 Dependencies Copy Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Create destination folder
if (Test-Path $destinationFolder) {
    Write-Host "Removing existing destination folder..." -ForegroundColor Yellow
    Remove-Item $destinationFolder -Recurse -Force
}

Write-Host "Creating destination folder: $destinationFolder" -ForegroundColor Green
New-Item -ItemType Directory -Path $destinationFolder -Force | Out-Null

# Create a summary file with file descriptions
$summaryContent = @"
PHASE 11 CRITICAL DEPENDENCIES - FILE SUMMARY
==============================================
Generated: $(Get-Date)

This folder contains the 20 most important files for implementing Phase 11:
Frontend API Integration & Sync Layer

FILES BY CATEGORY:
==================

1. CORE RBAC SERVICE:
   - services_rbac_service.py: Essential permission checking and role management logic

2. AUTHENTICATION & SECURITY (Files 2-4):
   - core_security.py: JWT, OAuth2, API key verification
   - core_dependencies.py: Dependency injection patterns
   - models_auth_router.py: Primary auth endpoints

3. RBAC & PERMISSIONS (Files 5-7):
   - schemas_auth_permissions.py: Permission definitions
   - schemas_security_permissions.py: Security permission schemas
   - schemas_security_api_keys.py: API key management

4. MIDDLEWARE & REQUEST PROCESSING (Files 8-10):
   - routers_middleware.py: Complete middleware stack (CORS, rate limiting, security)
   - routers_rate_limiter.py: Rate limiting implementation
   - routers_main.py: Main router aggregation

5. USER & SESSION MANAGEMENT (Files 11-13):
   - models_user.py: User model with auth fields
   - models_user_schemas.py: User Pydantic schemas
   - services_token_service.py: Token business logic

6. BASE SCHEMA PATTERNS (Files 14-16):
   - schemas_base_responses.py: Standard response formats
   - schemas_base_pagination.py: Pagination patterns
   - schemas_base_errors.py: Error response standardization

7. FOUNDATION (Files 17-20):
   - core_db_session.py: Database session management
   - core_config.py: Application configuration
   - core_exceptions.py: Custom exception handling
   - models_contract.py: Document/contract models

INTEGRATION NOTES:
==================
- services_rbac_service.py contains core permission checking logic for RBAC
- For complete Phase 10 implementations, see the original phase 10 code.md file
- This selection focuses on manageable, essential files for Phase 11 development

- Use routers_middleware.py patterns for Phase 11 middleware integration
- Follow schemas_base_* patterns for new frontend response schemas
- Reference auth patterns from models_auth_router.py for session handling

"@

$copyCount = 0
$missingFiles = @()

Write-Host "Copying files with flattened naming..." -ForegroundColor Green
Write-Host ""

foreach ($file in $criticalFiles) {
    $sourcePath = Join-Path $sourceRoot $file
    
    # Create flattened filename (replace path separators with underscores)
    $flattenedName = $file -replace '\\', '_' -replace '/', '_'
    $destinationPath = Join-Path $destinationFolder $flattenedName
    
    if (Test-Path $sourcePath) {
        try {
            Copy-Item $sourcePath $destinationPath -Force
            Write-Host "✓ Copied: $file -> $flattenedName" -ForegroundColor Green
            $copyCount++
        }
        catch {
            Write-Host "✗ Failed to copy: $file - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "✗ Missing: $file" -ForegroundColor Red
        $missingFiles += $file
    }
}

# Write summary file
$summaryPath = Join-Path $destinationFolder "README_PHASE11_DEPENDENCIES.txt"
$summaryContent | Out-File -FilePath $summaryPath -Encoding UTF8

Write-Host ""
Write-Host "COPY SUMMARY:" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan
Write-Host "Successfully copied: $copyCount files" -ForegroundColor Green
Write-Host "Missing files: $($missingFiles.Count)" -ForegroundColor $(if ($missingFiles.Count -gt 0) { "Red" } else { "Green" })

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing files:" -ForegroundColor Yellow
    foreach ($missing in $missingFiles) {
        Write-Host "  - $missing" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Files copied to: $destinationFolder" -ForegroundColor Cyan
Write-Host "Summary file created: README_PHASE11_DEPENDENCIES.txt" -ForegroundColor Cyan

# Create a quick reference index
$indexContent = @"
PHASE 11 QUICK REFERENCE INDEX
==============================

MOST CRITICAL FILES TO REVIEW FIRST:
=====================================
1. services_rbac_service.py - Core RBAC permission checking logic
2. routers_middleware.py - Middleware patterns for Phase 11 integration
3. core_security.py - Authentication foundation
4. schemas_base_responses.py - Response schema patterns
5. models_user.py - User model for profile management

IMPLEMENTATION ORDER RECOMMENDATION:
====================================
Phase 11.1: Frontend Response Schemas
- Review: schemas_base_* files
- Create: schemas/frontend/ directory with new response schemas

Phase 11.2: Unified API Router
- Review: routers_main.py, routers_middleware.py
- Create: routers/api/v2/frontend_sync.py

Phase 11.3: Real-Time Service
- Review: services_rbac_service.py, core_security.py for session patterns
- Create: services/realtime/ directory

Phase 11.4: Frontend Session Service
- Review: services_rbac_service.py for permission patterns
- Create: services/frontend_session/ directory

INTEGRATION PATTERNS:
====================
- RBAC: Use services_rbac_service.py patterns for permission checking
- Audit: Reference existing audit patterns for action logging
- Sessions: Use core_security.py patterns for session management
- Pagination: Follow schemas_base_pagination.py patterns
- Errors: Use schemas_base_errors.py for consistent error responses
- Notifications: Build on existing notification patterns for real-time updates

"@

$indexPath = Join-Path $destinationFolder "QUICK_REFERENCE.txt"
$indexContent | Out-File -FilePath $indexPath -Encoding UTF8

Write-Host "Quick reference created: QUICK_REFERENCE.txt" -ForegroundColor Cyan
Write-Host ""
Write-Host "Phase 11 dependency files ready for review!" -ForegroundColor Green
