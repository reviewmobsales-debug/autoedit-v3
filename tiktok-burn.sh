#!/bin/bash
# AutoEdit One-Shot — TikTok caption burn with ffmpeg drawtext
# No server, no Python, no Whisper. Just ffmpeg.
#
# Usage: ./tiktok-burn.sh input.mp4 "Your text here" output.mp4

set -e

INPUT="${1:-demo.mp4}"
TEXT="${2:-AutoEdit Demo}"
OUTPUT="${3:-tiktok_output.mp4}"

echo "🎬 AutoEdit One-Shot TikTok Burn"
echo "   Input:  $INPUT"
echo "   Text:   $TEXT"
echo "   Output: $OUTPUT"
echo ""

# Generate a 15-second colorful background if input doesn't exist
if [ ! -f "$INPUT" ]; then
    echo "⚠️ No input file found, generating 15s test video..."
    ffmpeg -f lavfi -i "color=c=0xFF0050:s=1080x1920:d=15" \
        -f lavfi -i "aevalsrc=0:d=15" \
        -shortest -y "$INPUT"
fi

# TikTok-style drawtext: white text, black stroke, centered
ffmpeg -y -i "$INPUT" \
    -vf "
      drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:
      text='$TEXT':
      fontcolor=white:
      fontsize=72:
      x=(w-text_w)/2:
      y=(h-text_h)/2+h*0.2:
      borderw=4:
      bordercolor=black@0.8:
      box=1:
      boxcolor=black@0.6:
      boxborderw=10
    " \
    -c:a copy \
    -c:v libx264 -preset fast -crf 23 \
    -pix_fmt yuv420p \
    -movflags +faststart \
    "$OUTPUT"

echo ""
echo "✅ Done: $OUTPUT"
ls -lh "$OUTPUT"
