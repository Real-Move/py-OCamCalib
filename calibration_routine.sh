#!/bin/bash

# --- Default values ---
SAVE_DIR="/root/py-OCamCalib/test_images"
WIDTH=640
HEIGHT=480
CAMERA_NAME="Elp"
CHESSBOARD_COLS=9
CHESSBOARD_ROWS=7
VIDEO_ID=""  # Empty means auto-detect
CONFIG_FILE="/root/py-OCamCalib/config.yaml"

# --- Parse CLI arguments ---
while [[ $# -gt 0 ]]; do
  KEY="$1"
  case $KEY in
    --config)           CONFIG_FILE="$2"; shift; shift ;;
    --save_dir)         SAVE_DIR="$2"; shift; shift ;;
    --width)            WIDTH="$2"; shift; shift ;;
    --height)           HEIGHT="$2"; shift; shift ;;
    --camera_name)      CAMERA_NAME="$2"; shift; shift ;;
    --chessboard_cols)  CHESSBOARD_COLS="$2"; shift; shift ;;
    --chessboard_rows)  CHESSBOARD_ROWS="$2"; shift; shift ;;
    --video_id)         VIDEO_ID="$2"; shift; shift ;;
    *) echo "❌ Unknown option: $1"; exit 1 ;;
  esac
done

# --- Build command ---
CMD=(python3 -u camera_calib_capture.py
  --camera_name "$CAMERA_NAME"
  --width "$WIDTH"
  --height "$HEIGHT"
  --chessboard_size_column "$CHESSBOARD_COLS"
  --chessboard_size_row "$CHESSBOARD_ROWS"
  --save_dir "$SAVE_DIR"
)

if [[ -n "$VIDEO_ID" ]]; then
  CMD+=(--video_id "$VIDEO_ID")
fi

# --- Execute command ---
"${CMD[@]}"

# --- Check latest folder ---
latest_folder=$(ls -td -- "$SAVE_DIR"/*/ 2>/dev/null | head -n 1)
echo "Selected folder: $latest_folder"

# Check if the folder is empty
if [[ -z "$latest_folder" || -z "$(ls -A "$latest_folder")" ]]; then
  echo "⚠️  Folder is empty. Deleting: $latest_folder"
  rm -rf "$latest_folder"
  echo "⏭️  Skipping calibration steps."
  exit 0
fi

# --- Run calibration ---
cd /root/py-OCamCalib
pip install -e . 2>/dev/null

python3 /root/py-OCamCalib/src/pyocamcalib/script/calibration_script.py "$latest_folder" ${CHESSBOARD_COLS} ${CHESSBOARD_ROWS} --camera-name "$CAMERA_NAME"
