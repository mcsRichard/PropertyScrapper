#!/bin/bash

echo "========================================"
echo "准备SCF部署包"
echo "========================================"
echo ""

# 检查是否在项目根目录
if [ ! -d "backend" ]; then
    echo "[错误] 请在项目根目录运行此脚本"
    exit 1
fi

# 创建部署目录
if [ ! -d "scf_deploy" ]; then
    mkdir -p scf_deploy
    echo "[创建] scf_deploy 目录"
fi

# 复制backend目录
if [ -d "scf_deploy/backend" ]; then
    echo "[删除] 旧的backend目录"
    rm -rf scf_deploy/backend
fi

echo "[复制] backend 目录..."
cp -r backend scf_deploy/

# 复制requirements.txt
echo "[复制] requirements.txt..."
cp backend/requirements.txt scf_deploy/

# 检查index.py是否存在
if [ ! -f "scf_deploy/index.py" ]; then
    echo "[警告] index.py 不存在，请确保已创建"
fi

echo ""
echo "========================================"
echo "部署包准备完成！"
echo "========================================"
echo ""
echo "部署包位置: scf_deploy/"
echo ""
echo "目录结构:"
echo "  scf_deploy/"
echo "  ├── index.py"
echo "  ├── backend/"
echo "  └── requirements.txt"
echo ""
echo "下一步: 在腾讯云控制台上传 scf_deploy 目录"
echo ""

