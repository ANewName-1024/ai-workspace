#!/bin/bash
# Whisper 语音转文字 - 按需加载模型
# 用法: whisper-transcribe.sh <音频文件路径>

export http_proxy=http://192.168.2.22:7890
export https_proxy=http://192.168.2.22:7890
export HTTP_PROXY=http://192.168.2.22:7890
export HTTPS_PROXY=http://192.168.2.22:7890

AUDIO_FILE="$1"

if [ -z "$AUDIO_FILE" ]; then
    echo "用法: whisper-transcribe.sh <音频文件路径>"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "文件不存在: $AUDIO_FILE"
    exit 1
fi

echo "正在加载模型并转录..."

source /root/.openclaw/workspace/.venv/bin/activate

python3 << 'EOF'
import sys
from faster_whisper import WhisperModel

try:
    model = WhisperModel("tiny", device="cpu")
    segments, info = model.transcribe("/root/.openclaw/workspace/$AUDIO_FILE", language="zh")
    
    print("识别结果:")
    for segment in segments:
        print(segment.text, end="")
    print()
except Exception as e:
    print(f"错误: {e}", file=sys.stderr)
    sys.exit(1)
EOF
