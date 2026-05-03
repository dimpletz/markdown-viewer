#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test v1.3.3 → v1.3.5 upgrade scenario to verify server auto-restart fix.

.DESCRIPTION
    Simulates the exact user scenario:
    1. Install v1.3.3 (old version without vendor route)
    2. Start server on port 5050
    3. Upgrade to v1.3.5 (new wheel from dist/)
    4. Run mdview - should detect old server and restart it
    5. Verify vendor files return 200 (not 404)

.EXAMPLE
    .\test_upgrade_scenario.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-Step {
    param([string]$Message)
    Write-Host "${Blue}▶ ${Message}${Reset}"
}

function Write-Success {
    param([string]$Message)
    Write-Host "${Green}✓ ${Message}${Reset}"
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "${Red}✗ ${Message}${Reset}"
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "${Yellow}⚠ ${Message}${Reset}"
}

# Cleanup function
function Cleanup {
    Write-Step "Cleaning up test environment..."
    
    # Kill any Python processes on test port
    Get-Process -Name python -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $_ | Stop-Process -Force
            Write-Warning-Custom "Killed Python process $($_.Id)"
        } catch {}
    }
    
    # Remove test venvs
    if (Test-Path "test_venv_old") {
        Remove-Item -Recurse -Force "test_venv_old"
        Write-Success "Removed test_venv_old"
    }
    if (Test-Path "test_venv_new") {
        Remove-Item -Recurse -Force "test_venv_new"
        Write-Success "Removed test_venv_new"
    }
    
    # Remove test PID file
    $pidFile = Join-Path $env:TEMP "mdview-5050.pid"
    if (Test-Path $pidFile) {
        Remove-Item -Force $pidFile
        Write-Success "Removed PID file"
    }
    
    # Remove test markdown file
    if (Test-Path "test_upgrade.md") {
        Remove-Item -Force "test_upgrade.md"
        Write-Success "Removed test file"
    }
}

# Ensure we start clean
Cleanup

try {
    Write-Host "${Green}═══════════════════════════════════════════════════════════${Reset}"
    Write-Host "${Green}  Testing v1.3.3 → v1.3.5 Upgrade Scenario${Reset}"
    Write-Host "${Green}═══════════════════════════════════════════════════════════${Reset}"
    Write-Host ""

    # Step 1: Create test markdown file
    Write-Step "Step 1: Creating test markdown file..."
    @"
# Test Upgrade Scenario

This is a test file to verify vendor file loading after upgrade.

## Mermaid Diagram
\`\`\`mermaid
graph TD
    A[v1.3.3 Running] --> B[Upgrade to v1.3.5]
    B --> C{Old Server?}
    C -->|Yes| D[Auto-Restart]
    C -->|No| E[Start Fresh]
    D --> F[Vendor Files Load ✓]
    E --> F
\`\`\`

## Math (KaTeX)
$$E = mc^2$$
"@ | Out-File -FilePath "test_upgrade.md" -Encoding UTF8
    Write-Success "Created test_upgrade.md"
    Write-Host ""

    # Step 2: Install OLD version (v1.3.3 - before vendor route was added)
    Write-Step "Step 2: Installing OLD version (v1.3.3) in test_venv_old..."
    python -m venv test_venv_old
    & .\test_venv_old\Scripts\Activate.ps1
    pip install --quiet markdown-viewer-app==1.3.3
    Write-Success "Installed v1.3.3"
    
    # Verify old version
    $oldVersion = python -c "from markdown_viewer import __version__; print(__version__)"
    if ($oldVersion -ne "1.3.3") {
        throw "Expected v1.3.3, got v$oldVersion"
    }
    Write-Success "Verified version: $oldVersion"
    Write-Host ""

    # Step 3: Start OLD server on port 5050 (NO vendor route)
    Write-Step "Step 3: Starting OLD server (v1.3.3) on port 5050..."
    $serverJob = Start-Job -ScriptBlock {
        param($venvPath)
        & "$venvPath\Scripts\Activate.ps1"
        python -c "from markdown_viewer.server import run_flask_app; run_flask_app(port=5050, use_reloader=False)"
    } -ArgumentList (Resolve-Path "test_venv_old")
    
    Write-Success "Server job started (ID: $($serverJob.Id))"
    
    # Wait for old server to start
    Write-Host "  Waiting for old server to start..."
    $serverReady = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5050/api/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $serverReady = $true
                break
            }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    
    if (-not $serverReady) {
        throw "Old server failed to start"
    }
    Write-Success "Old server is UP on port 5050"
    Write-Host ""

    # Step 4: Verify OLD server DOES NOT have vendor route (should 404)
    Write-Step "Step 4: Verifying OLD server lacks vendor route..."
    try {
        $vendorResponse = Invoke-WebRequest -Uri "http://localhost:5050/vendor/purify.min.js" -ErrorAction Stop
        Write-Error-Custom "OLD server has vendor route (unexpected!)"
        throw "Test setup failed: v1.3.3 should not have vendor route"
    } catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Success "Confirmed: OLD server returns 404 for vendor files (expected)"
        } else {
            throw "Unexpected error checking vendor route: $_"
        }
    }
    Write-Host ""

    # Step 5: Deactivate old venv and create NEW venv
    Write-Step "Step 5: Creating NEW environment (v1.3.5)..."
    deactivate
    python -m venv test_venv_new
    & .\test_venv_new\Scripts\Activate.ps1
    Write-Success "Created test_venv_new"
    Write-Host ""

    # Step 6: Install NEW version from local wheel
    Write-Step "Step 6: Installing NEW version (v1.3.5) from local wheel..."
    if (-not (Test-Path "dist\markdown_viewer_app-1.3.5-py3-none-any.whl")) {
        throw "Wheel not found! Run 'poetry build' first."
    }
    pip install --quiet --force-reinstall "dist\markdown_viewer_app-1.3.5-py3-none-any.whl"
    Write-Success "Installed v1.3.5 from local wheel"
    
    # Verify new version
    $newVersion = python -c "from markdown_viewer import __version__; print(__version__)"
    if ($newVersion -ne "1.3.5") {
        throw "Expected v1.3.5, got v$newVersion"
    }
    Write-Success "Verified version: $newVersion"
    Write-Host ""

    # Step 7: Verify NEW package has vendor files
    Write-Step "Step 7: Verifying NEW package contains vendor files..."
    $vendorCheck = python -c @"
import os
import markdown_viewer
pkg_dir = os.path.dirname(markdown_viewer.__file__)
vendor_dir = os.path.join(pkg_dir, 'electron', 'renderer', 'vendor')
mermaid_file = os.path.join(vendor_dir, 'mermaid', 'mermaid.min.js')
print('EXISTS' if os.path.exists(mermaid_file) else 'MISSING')
"@
    if ($vendorCheck -ne "EXISTS") {
        throw "Vendor files missing from v1.3.5 package!"
    }
    Write-Success "Vendor files present in package"
    Write-Host ""

    # Step 8: THE CRITICAL TEST - Run mdview with OLD server still running
    Write-Step "Step 8: Running 'mdview' with OLD server still active..."
    Write-Host "  ${Yellow}This should trigger auto-restart logic...${Reset}"
    Write-Host ""
    
    # Start mdview in background with output capture
    $mdviewOutput = ""
    $mdviewJob = Start-Job -ScriptBlock {
        param($venvPath, $testFile)
        & "$venvPath\Scripts\Activate.ps1"
        $env:BACKEND_PORT = "5050"
        python -c @"
from markdown_viewer.cli import _open_in_flask_app
from pathlib import Path
_open_in_flask_app(Path('$testFile'), port=5050, browser=None)
"@ 2>&1
    } -ArgumentList (Resolve-Path "test_venv_new"), (Resolve-Path "test_upgrade.md")
    
    # Wait for restart to complete
    Start-Sleep -Seconds 5
    
    # Get job output
    $mdviewOutput = Receive-Job -Job $mdviewJob
    Write-Host "  mdview output:"
    $mdviewOutput | ForEach-Object { Write-Host "    $_" }
    Write-Host ""
    
    # Check if restart message appeared
    if ($mdviewOutput -match "Outdated server detected") {
        Write-Success "✓ Detected outdated server message"
    } else {
        Write-Warning-Custom "Auto-restart message not shown (may have started fresh)"
    }
    Write-Host ""

    # Step 9: Verify NEW server has vendor route (should 200)
    Write-Step "Step 9: Verifying NEW server serves vendor files..."
    Start-Sleep -Seconds 2  # Give server time to restart
    
    $vendorTests = @(
        "purify.min.js",
        "marked/marked.min.js",
        "mermaid/mermaid.min.js",
        "katex/katex.min.js",
        "axios/axios.min.js"
    )
    
    $allPassed = $true
    foreach ($file in $vendorTests) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5050/vendor/$file" -Method Head -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Success "  ✓ /vendor/$file → 200 OK"
            } else {
                Write-Error-Custom "  ✗ /vendor/$file → $($response.StatusCode)"
                $allPassed = $false
            }
        } catch {
            Write-Error-Custom "  ✗ /vendor/$file → ERROR: $($_.Exception.Message)"
            $allPassed = $false
        }
    }
    Write-Host ""

    # Step 10: Test actual page load
    Write-Step "Step 10: Testing full page load..."
    try {
        $pageResponse = Invoke-WebRequest -Uri "http://localhost:5050/" -ErrorAction Stop
        if ($pageResponse.StatusCode -eq 200) {
            Write-Success "  ✓ Index page loads (200 OK)"
            
            # Check if vendor scripts are in HTML
            $html = $pageResponse.Content
            if ($html -match 'vendor/mermaid/mermaid\.min\.js') {
                Write-Success "  ✓ HTML contains vendor script references"
            } else {
                Write-Warning-Custom "  ! Vendor scripts not found in HTML"
            }
        }
    } catch {
        Write-Error-Custom "  ✗ Index page failed: $_"
        $allPassed = $false
    }
    Write-Host ""

    # Final Result
    Write-Host "${Green}═══════════════════════════════════════════════════════════${Reset}"
    if ($allPassed) {
        Write-Host "${Green}  ✓ ALL TESTS PASSED!${Reset}"
        Write-Host "${Green}  v1.3.5 upgrade scenario works correctly.${Reset}"
        Write-Host "${Green}  Safe to publish!${Reset}"
    } else {
        Write-Host "${Red}  ✗ SOME TESTS FAILED!${Reset}"
        Write-Host "${Red}  DO NOT PUBLISH - Fix issues first.${Reset}"
    }
    Write-Host "${Green}═══════════════════════════════════════════════════════════${Reset}"

} catch {
    Write-Host ""
    Write-Host "${Red}═══════════════════════════════════════════════════════════${Reset}"
    Write-Host "${Red}  ✗ TEST FAILED WITH ERROR${Reset}"
    Write-Host "${Red}═══════════════════════════════════════════════════════════${Reset}"
    Write-Host "${Red}Error: $_${Reset}"
    Write-Host "${Red}$($_.ScriptStackTrace)${Reset}"
    Write-Host ""
    exit 1
} finally {
    Write-Host ""
    Cleanup
    Write-Host "${Blue}Test complete.${Reset}"
}
