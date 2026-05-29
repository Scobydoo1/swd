<#
.SYNOPSIS
    Khởi động lại sạch backend + frontend của Course RAG Chatbot.

.DESCRIPTION
    - Dừng triệt để tiến trình cũ trên cổng backend/frontend (kill cả cây tiến
      trình bằng taskkill /T để KHÔNG để lại socket mồ côi giữ cổng).
    - Chờ cổng được nhả hẳn.
    - Mở 2 cửa sổ mới chạy backend (uvicorn) và frontend (vite).

.EXAMPLE
    ./restart.ps1
    ./restart.ps1 -BackendPort 8000
#>
param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Stop-Port([int]$port) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if (-not $conns) { Write-Host "  Cổng ${port}: trống." -ForegroundColor DarkGray; return }

    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -and $_ -ne 0 }
    foreach ($procId in $pids) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Cổng ${port}: dừng PID $procId ($($proc.ProcessName)) + tiến trình con..." -ForegroundColor Yellow
            # /T kill cả cây tiến trình -> reloader của uvicorn không spawn lại,
            # tránh để lại socket LISTEN mồ côi.
            taskkill /PID $procId /T /F 2>$null | Out-Null
        } else {
            Write-Host "  Cổng ${port}: PID $procId đã chết nhưng socket còn treo (zombie). Cần reboot để dọn." -ForegroundColor Red
        }
    }
}

function Wait-PortFree([int]$port, [int]$timeoutSec = 20) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        $listen = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $listen) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

Write-Host "==> Dừng tiến trình cũ..." -ForegroundColor Cyan
Stop-Port $BackendPort
Stop-Port $FrontendPort

Write-Host "==> Chờ cổng nhả..." -ForegroundColor Cyan
$beOk = Wait-PortFree $BackendPort
$feOk = Wait-PortFree $FrontendPort
if (-not $beOk) {
    Write-Host "!! Cổng $BackendPort vẫn bị giữ (zombie socket). Thử cổng khác hoặc reboot." -ForegroundColor Red
    Write-Host "   Ví dụ: ./restart.ps1 -BackendPort 8002  (nhớ sửa proxy trong frontend/vite.config.ts cho khớp)" -ForegroundColor Red
    exit 1
}

# Đồng bộ cổng proxy của frontend với cổng backend đang dùng.
$viteConfig = Join-Path $root "frontend/vite.config.ts"
if (Test-Path $viteConfig) {
    $content = Get-Content $viteConfig -Raw
    $patched = $content -replace '"/api":\s*"http://localhost:\d+"', "`"/api`": `"http://localhost:$BackendPort`""
    if ($patched -ne $content) {
        Set-Content $viteConfig $patched -Encoding utf8 -NoNewline
        Write-Host "==> Đã cập nhật proxy frontend -> :$BackendPort" -ForegroundColor Cyan
    }
}

Write-Host "==> Khởi động backend (cổng $BackendPort)..." -ForegroundColor Green
$backendDir = Join-Path $root "backend"
$venvPy = Join-Path $backendDir ".venv/Scripts/python.exe"
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$backendDir'; & '$venvPy' -m uvicorn app.main:app --reload --port $BackendPort"
)

Write-Host "==> Khởi động frontend (cổng $FrontendPort)..." -ForegroundColor Green
$frontendDir = Join-Path $root "frontend"
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$frontendDir'; npm run dev"
)

Write-Host ""
Write-Host "Xong! Mở:  http://localhost:$FrontendPort" -ForegroundColor Green
