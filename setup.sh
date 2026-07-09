#!/bin/bash

# 1. 终止可能残存的 ollama 进程
echo "========== 清理旧环境 =========="
sudo systemctl stop ollama || true

# 2. 一键安装 Ollama
echo "========== 开始安装 Ollama =========="
curl -fsSL https://ollama.com/install.sh | sh

# 3. 强行在后台启动 Ollama 服务（防止单次阻塞）
echo "========== 启动 Ollama 后台服务 =========="
sudo systemctl start ollama

# 4. 预先拉取 0.5B 安全模型（静默下载，不占用交互终端）
echo "========== 正在下载 0.5B 超轻量安全模型 (约300MB) =========="
echo "提示：此模型专为 Killercoda 优化，绝不爆内存、不锁死CPU！"
ollama pull qwen2.5:0.5b

echo "========== 部署完成！=========="
echo "现在你可以直接运行以下命令开启 AI 对话了："
echo "ollama run qwen2.5:0.5b"
