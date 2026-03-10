#!/bin/bash
# 代理配置脚本
# 使用方法: source scripts/setup-proxy.sh

# 配置代理地址（替换为你的实际代理）
# 方式一：HTTP/HTTPS 代理
# export http_proxy="http://你的代理IP:端口"
# export https_proxy="http://你的代理IP:端口"

# 方式二：SOCKS5 代理
# export socks_proxy="socks5://你的代理IP:端口"

# 方式三：从环境变量读取（推荐）
if [ -n "$PROXY_URL" ]; then
    export http_proxy="$PROXY_URL"
    export https_proxy="$PROXY_URL"
    export HTTP_PROXY="$PROXY_URL"
    export HTTPS_PROXY="$PROXY_URL"
    echo "代理已配置: $PROXY_URL"
else
    # 默认使用 Windows 代理（WSL 访问 Windows 代理）
    export http_proxy="http://192.168.2.22:7890"
    export https_proxy="http://192.168.2.22:7890"
    export HTTP_PROXY="http://192.168.2.22:7890"
    export HTTPS_PROXY="http://192.168.2.22:7890"
    echo "使用默认 Windows 代理: 192.168.2.22:7890"
fi

# 为 Python 设置代理
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export http_proxy="$http_proxy"
export https_proxy="$https_proxy"

echo "代理配置完成"
