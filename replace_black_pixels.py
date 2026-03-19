"""
Create a transparent animation by removing "black" pixels (set alpha=0),
then encode to formats that browsers can play.

Usage:
    python3 replace_black_pixels.py

Input:  assets/images/test.mov (original — untouched)

Outputs:
  - assets/images/test_transparent.webm (recommended; alpha supported)
  - assets/images/test_transparent.gif  (legacy; may show minor fringing)

Implementation detail:
  - We treat "black" as pixels where ALL channels (B,G,R) are below TRANSPARENT_BLACK_THRESHOLD.
  - GIF transparency is palette-based, so quantization may introduce halos.
"""

import cv2
import numpy as np
import os
import subprocess
import tempfile
from pathlib import Path

INPUT  = "/Users/pedrambeigi/xPEDRAMx.github.io/assets/images/test.mov"
OUTPUT = "/Users/pedrambeigi/xPEDRAMx.github.io/assets/images/test_processed.mp4"

# Target: exact website background #1b1035 (RGB 27,16,53) measured from screenshot.
# Pre-compensated for yuv420p H.264 encoding drift (~R-3, G+1, B-4):
# write RGB(30, 15, 57) → encoded output lands on RGB(27, 16, 53) = #1b1035
TARGET_COLOR_BGR = (35, 10, 15)   # BGR for OpenCV

# Any pixel where ALL three channels are below this value → replaced (old mode)
REPLACE_BLACK_THRESHOLD = 60

# For transparency: background pixels are around RGB(~8,4,18) in test.mov,
# so 20 removes the background while keeping the brighter content.
TRANSPARENT_BLACK_THRESHOLD = 20

OUTPUT_WEBM = "/Users/pedrambeigi/xPEDRAMx.github.io/assets/images/test_transparent.webm"
OUTPUT_GIF  = "/Users/pedrambeigi/xPEDRAMx.github.io/assets/images/test_transparent.gif"


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

    print(
        f"Processing {total} frames  ({width}x{height} @ {fps:.1f} fps)  threshold={REPLACE_BLACK_THRESHOLD}"
    )

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Replace pixels where every channel is below the threshold
        mask = np.all(frame < REPLACE_BLACK_THRESHOLD, axis=2)
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


def write_transparent_frames(input_path: str, out_dir: str) -> tuple[float, int, int, int]:
    """
    Write RGBA PNG frames where "black" pixels get alpha=0.

    Returns: (fps, width, height, frame_count)
    """
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or -1)

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    frame_idx = 0
    print(
        f"Writing transparent RGBA frames  ({width}x{height} @ {fps:.2f} fps) "
        f"threshold={TRANSPARENT_BLACK_THRESHOLD}"
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # frame is BGR
        mask = np.all(frame < TRANSPARENT_BLACK_THRESHOLD, axis=2)  # HxW bool
        alpha = np.where(mask, 0, 255).astype(np.uint8)  # HxW
        rgb = frame[:, :, ::-1]  # BGR -> RGB
        rgba = np.dstack([rgb, alpha])  # HxWx4

        # cv2.imwrite expects BGRA ordering, so convert back.
        png_path = out_path / f"frame_{frame_idx:05d}.png"
        cv2.imwrite(str(png_path), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))

        frame_idx += 1
        if total > 0 and frame_idx % 50 == 0:
            print(f"  {frame_idx}/{total} frames…")

    cap.release()
    print(f"Done writing {frame_idx} frames to {out_dir}")
    return fps, width, height, frame_idx


def encode_webm_alpha(png_dir: str, fps: float, out_path: str) -> None:
    png_dir_path = Path(png_dir)
    input_pattern = str(png_dir_path / "frame_%05d.png")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        input_pattern,
        "-c:v",
        "libvpx-vp9",
        "-pix_fmt",
        "yuva420p",
        "-auto-alt-ref",
        "0",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg stderr (webm):\n", result.stderr[-1200:])
        raise RuntimeError("webm encode failed")


def encode_gif_transparent(png_dir: str, fps: float, out_path: str) -> None:
    """
    Encode GIF from RGBA frames.

    GIF transparency is palette-based; fringing is possible but this gives you a usable file quickly.
    """
    png_dir_path = Path(png_dir)
    input_pattern = str(png_dir_path / "frame_%05d.png")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        input_pattern,
        "-filter_complex",
        "[0:v]split[a][b];[a]palettegen=reserve_transparent=1:transparency_color=black[p];[b][p]paletteuse=alpha_threshold=1",
        "-loop",
        "0",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg stderr (gif):\n", result.stderr[-1200:])
        raise RuntimeError("gif encode failed")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        fps, w, h, frame_count = write_transparent_frames(INPUT, tmpdir)
        encode_webm_alpha(tmpdir, fps, OUTPUT_WEBM)
        print(f"✅ WebM with alpha saved → {OUTPUT_WEBM}")

        try:
            encode_gif_transparent(tmpdir, fps, OUTPUT_GIF)
            print(f"✅ GIF saved → {OUTPUT_GIF}")
        except RuntimeError:
            print("GIF encode failed; keeping only the .webm output.")
