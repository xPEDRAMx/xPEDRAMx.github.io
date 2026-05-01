#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PDF="/Users/pedrambeigi/xPEDRAMx.github.io/resume/resume.pdf"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --disable-gpu \
  --allow-file-access-from-files \
  --no-pdf-header-footer \
  --print-to-pdf="${OUTPUT_PDF}" \
  "file:///Users/pedrambeigi/xPEDRAMx.github.io/resume/index.html"
