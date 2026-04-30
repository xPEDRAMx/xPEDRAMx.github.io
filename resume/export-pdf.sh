#!/usr/bin/env bash
set -euo pipefail

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --disable-gpu \
  --allow-file-access-from-files \
  --print-to-pdf="/Users/pedrambeigi/xPEDRAMx.github.io/resume/resume.pdf" \
  "file:///Users/pedrambeigi/xPEDRAMx.github.io/resume/index.html"
