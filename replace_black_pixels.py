"""
Replace near-black pixels in a video with the site's background color (#0a0514),
then re-encode to H.264 so browsers can play it.

Usage:
    python3 replace_black_pixels.py

Input:  assets/images/test.mp4          (original — untouched)
Output: assets/images/test_processed.mp4 (new file)

The "black threshold" controls how dark a pixel must be to be replaced.
Raise it to catch dark-grey pixels too; lower it for pure-black only.
"""

import cv2
import numpy as np
import os
import subprocess
import tempfile

INPUT  = "/Users/pedrambeigi/xPEDRAMx.github.io/assets/images/test.mov"
OUTPUT = "/Users/pedrambeigi/xPEDRAMx.github.io/assets/images/test_processed.mp4"

# Target: exact website background #1b1035 (RGB 27,16,53) measured from screenshot.
# Pre-compensated for yuv420p H.264 encoding drift (~R-3, G+1, B-4):
# write RGB(30, 15, 57) → encoded output lands on RGB(27, 16, 53) = #1b1035
TARGET_COLOR_BGR = (35, 10, 15)   # BGR for OpenCV

# Any pixel where ALL three channels are below this value → replaced
# 60 catches near-black and very dark colours, not just pure black
BLACK_THRESHOLD = 60


def replace_black_pixels(input_path: str, raw_output: str) -> None:
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fps    = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out    = cv2.VideoWriter(raw_output, fourcc, fps, (width, height))

    fill = np.array(TARGET_COLOR_BGR, dtype=np.uint8)

    print(f"Processing {total} frames  ({width}x{height} @ {fps:.1f} fps)  threshold={BLACK_THRESHOLD}")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Replace pixels where every channel is below the threshold
        mask = np.all(frame < BLACK_THRESHOLD, axis=2)
        frame[mask] = fill

        out.write(frame)
        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"  {frame_idx}/{total} frames…")

    cap.release()
    out.release()
    print(f"Raw frames written → {raw_output}")


def reencode_h264(raw_path: str, final_path: str) -> None:
    """Re-encode mp4v → H.264 so every browser can play it."""
    print("Re-encoding to H.264…")
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_path,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-movflags", "+faststart",
        final_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg stderr:\n", result.stderr[-800:])
        raise RuntimeError("ffmpeg failed")
    print(f"H.264 file saved → {final_path}")


if __name__ == "__main__":
    with tempfile.NamedTemporaryFile(suffix="_raw.mp4", delete=False) as tmp:
        raw_path = tmp.name

    try:
        replace_black_pixels(INPUT, raw_path)
        reencode_h264(raw_path, OUTPUT)
        print(f"\n✅ Done!\n   Original : {INPUT}\n   Processed: {OUTPUT}")
    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)
