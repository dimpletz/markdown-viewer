#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Simple local test for vendor file serving in v1.3.5

.DESCRIPTION
    Tests that the current v1.3.5 code properly serves vendor files
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "`n=== Testing v1.3.5 Vendor File Serving ===`n" -ForegroundColor Cyan

# Cleanup function
function Cleanup {
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*5051*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    if (Test-Path "test_simple_venv") {
        Remove-Item -Recurse -Force "test_simple_venv"
    }
    if (Test-Path "test_simple.md") {
        Remove-Item -Force "test_simple.md"
    }
}

# Start clean
Cleanup

try {
    # 1. Create test file
    Write-Host "1. Creating test markdown file..." -ForegroundColor Green
    @"
# Vendor Test
Test mermaid:
\`\`\`mermaid
graph TD;
    A-->B;
\`\`\`
"@ | Out-File -FilePath "test_simple.md" -Encoding UTF8
    Write-Host "   ✓ Created test_simple.md`n"

    # 2. Install current code
    Write-Host "2. Installing current v1.3.5 code..." -ForegroundColor Green
    python -m venv test_simple_venv
    & .\test_simple_venv\Scripts\Activate.ps1
    pip install --quiet -e .
    $version = python -c "from markdown_viewer import __version__; print(__version__)"
    Write-Host "   ✓ Installed version: $version`n"

    # 3. Start server
    Write-Host "3. Starting server on port 5051..." -ForegroundColor Green
    $serverJob = Start-Job -ScriptBlock {
        param($venvPath)
        & "$venvPath\Scripts\Activate.ps1"
        python -c "from markdown_viewer.server import run_flask_app; run_flask_app(port=5051, use_reloader=False)"
    } -ArgumentList (Resolve-Path "test_simple_venv")

    # Wait for server
    Write-Host "   Waiting for server to start..."
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:5051/api/health" -TimeoutSec 1 -ErrorAction Stop
            $ready = $true
            break
        } catch {}
        Start-Sleep -Milliseconds 500
    }

    if (-not $ready) {
        throw "Server failed to start"
    }
    Write-Host "   ✓ Server is UP`n" -ForegroundColor Green

    # 4. Test vendor files
    Write-Host "4. Testing vendor files..." -ForegroundColor Green
    $tests = @{
        "/vendor/purify.min.js" = "DOMPurify"
        "/vendor/marked/marked.min.js" = "Marked"
        "/vendor/mermaid/mermaid.min.js" = "Mermaid"
        "/vendor/katex/katex.min.js" = "KaTeX"
        "/vendor/katex/katex.min.css" = "KaTeX CSS"
        "/vendor/highlightjs/highlight.min.js" = "Highlight.js"
        "/vendor/axios/axios.min.js" = "Axios"
    }

    $passed = 0
    $failed = 0

    foreach ($path in $tests.Keys) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5051$path" -Method Head -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "   ✓ $($tests[$path]): 200 OK" -ForegroundColor Green
                $passed++
            } else {
                Write-Host "   ✗ $($tests[$path]): $($response.StatusCode)" -ForegroundColor Red
                $failed++
            }
        } catch {
            Write-Host "   ✗ $($tests[$path]): ERROR - $($_.Exception.Message)" -ForegroundColor Red
            $failed++
        }
    }

    # 5. Test index page
    Write-Host "`n5. Testing index page..." -ForegroundColor Green
    try {
        $pageResp = Invoke-WebRequest -Uri "http://localhost:5051/" -ErrorAction Stop
        if ($pageResp.StatusCode -eq 200 -and $pageResp.Content -match 'vendor/mermaid/mermaid\.min\.js') {
            Write-Host "   ✓ Index page loads with vendor scripts" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "   ✗ Index page issues" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "   ✗ Index page error: $_" -ForegroundColor Red
        $failed++
    }

    # Results
    Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
    if ($failed -eq 0) {
        Write-Host "✓ ALL TESTS PASSED ($passed/$($passed + $failed))" -ForegroundColor Green
        Write-Host "✓ Vendor files serve correctly in v1.3.5" -ForegroundColor Green
        Write-Host "✓ SAFE TO PUBLISH!" -ForegroundColor Green
        $exitCode = 0
    } else {
        Write-Host "✗ TESTS FAILED ($failed failed, $passed passed)" -ForegroundColor Red
        Write-Host "✗ DO NOT PUBLISH - FIX ISSUES FIRST" -ForegroundColor Red
        $exitCode = 1
    }
    Write-Host ("=" * 50 + "`n") -ForegroundColor Cyan

    exit $exitCode

} catch {
    Write-Host "`n✗ TEST ERROR: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
} finally {
    Cleanup
}
