# 准备云函数部署包脚本
# 使用方法：在项目根目录执行 .\scf_deploy\准备部署包.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "准备云函数部署包" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在项目根目录
if (-not (Test-Path "backend")) {
    Write-Host "错误：未找到backend目录，请在项目根目录执行此脚本" -ForegroundColor Red
    exit 1
}

# 创建scf_deploy目录（如果不存在）
$deployDir = "scf_deploy"
if (-not (Test-Path $deployDir)) {
    New-Item -ItemType Directory -Path $deployDir | Out-Null
    Write-Host "创建目录: $deployDir" -ForegroundColor Green
}

# 创建backend目录
$backendDeployDir = Join-Path $deployDir "backend"
if (Test-Path $backendDeployDir) {
    Write-Host "清理旧的backend目录..." -ForegroundColor Yellow
    Remove-Item -Path $backendDeployDir -Recurse -Force
}
New-Item -ItemType Directory -Path $backendDeployDir | Out-Null
Write-Host "创建目录: $backendDeployDir" -ForegroundColor Green

# 复制backend目录（排除__pycache__和.env）
Write-Host ""
Write-Host "复制backend目录..." -ForegroundColor Yellow
$excludeItems = @("__pycache__", "*.pyc", ".env")
Get-ChildItem -Path "backend" -Recurse | Where-Object {
    $item = $_
    $shouldExclude = $false
    foreach ($exclude in $excludeItems) {
        if ($item.Name -like $exclude -or $item.FullName -like "*$exclude*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
} | ForEach-Object {
    $relativePath = $_.FullName.Substring((Resolve-Path "backend").Path.Length + 1)
    $destPath = Join-Path $backendDeployDir $relativePath
    $destDir = Split-Path $destPath -Parent
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item -Path $_.FullName -Destination $destPath -Force
}

Write-Host "✓ backend目录复制完成" -ForegroundColor Green

# 复制requirements.txt
Write-Host ""
Write-Host "复制requirements.txt..." -ForegroundColor Yellow
Copy-Item -Path "backend\requirements.txt" -Destination "$deployDir\requirements.txt" -Force
Write-Host "✓ requirements.txt复制完成" -ForegroundColor Green

# 检查index.py是否存在
Write-Host ""
if (Test-Path "$deployDir\index.py") {
    Write-Host "✓ index.py已存在" -ForegroundColor Green
}
else {
    Write-Host "警告：未找到index.py，请确保已创建" -ForegroundColor Yellow
}

# 复制scf_bootstrap
Write-Host ""
if (Test-Path "scf_bootstrap") {
    Copy-Item -Path "scf_bootstrap" -Destination "$deployDir\scf_bootstrap" -Force
    Write-Host "✓ scf_bootstrap复制完成" -ForegroundColor Green
}
else {
    Write-Host "警告：未找到scf_bootstrap，请确保已创建" -ForegroundColor Yellow
}

# 显示部署包结构
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "部署包准备完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "部署包结构：" -ForegroundColor Yellow
Write-Host "  scf_deploy/" -ForegroundColor White
Write-Host "  ├── index.py" -ForegroundColor White
Write-Host "  ├── requirements.txt" -ForegroundColor White
Write-Host "  ├── scf_bootstrap" -ForegroundColor White
Write-Host "  └── backend/" -ForegroundColor White
Write-Host "      ├── app.py" -ForegroundColor White
Write-Host "      ├── config.py" -ForegroundColor White
Write-Host "      ├── api/" -ForegroundColor White
Write-Host "      ├── models/" -ForegroundColor White
Write-Host "      └── utils/" -ForegroundColor White
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 登录腾讯云控制台" -ForegroundColor White
Write-Host "2. 进入云函数SCF服务" -ForegroundColor White
Write-Host "3. 创建或选择函数" -ForegroundColor White
Write-Host "4. 上传 scf_deploy 目录" -ForegroundColor White
Write-Host ""
Write-Host "详细步骤请参考：scf_deploy\完整部署步骤.md" -ForegroundColor Cyan
Write-Host ""
