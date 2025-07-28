#!/usr/bin/env python3

import cv2
import os
import subprocess
import re
import numpy as np
from datetime import datetime
import argparse
import yaml

# ------------ CONSTANTS ------------
PIXEL_DISTANCE_THRESHOLD = 50  # in pixels

def get_external_camera_id():
    result = subprocess.run(['v4l2-ctl', '--list-devices'],
                            stdout=subprocess.PIPE, text=True)
    lines = result.stdout.splitlines()

    current_device = None
    devices = {}

    for line in lines:
        if line.strip() == "":
            continue
        if not line.startswith('\t'):
            current_device = line.strip()
            devices[current_device] = []
        else:
            dev_path = line.strip()
            if dev_path.startswith("/dev/video"):
                devices[current_device].append(dev_path)

    for name, paths in devices.items():
        if "Integrated" not in name and paths:
            video_dev = paths[0]
            camera_id = int(re.search(r'/dev/video(\d+)', video_dev).group(1))
            print(f"Using camera: {name} ({video_dev})")
            return camera_id

    raise RuntimeError("No external (non-integrated) camera found.")

def parse_args():
    parser = argparse.ArgumentParser(description="Capture chessboard images for calibration")

    parser.add_argument('--config', type=str, default="/root/py-OCamCalib/config.yaml", help="Path to YAML config file")

    parser.add_argument('--camera_name', type=str, default="Elp", help="Camera name prefix for images")
    parser.add_argument('--width', type=int, default=640, help="Camera resolution width")
    parser.add_argument('--height', type=int, default=480, help="Camera resolution height")
    parser.add_argument('--save_dir', type=str, default="test_images", help="Directory to save captured images")
    parser.add_argument('--chessboard_size_column', type=int, default=9, help="Number of inner corners per chessboard row")
    parser.add_argument('--chessboard_size_row', type=int, default=7, help="Number of inner corners per chessboard column")
    parser.add_argument('--video_id', type=int, help="Video device ID (e.g., 0 for /dev/video0). If not provided, tries to auto-detect.")

    # First parse CLI args
    args = parser.parse_args()

    # If config file is given, override everything
    if args.config:
        if os.path.exists(args.config):
            print(f"📄 Loading configuration from: {args.config}")
            with open(args.config, "r") as f:
                config_data = yaml.safe_load(f) or {}
                for key, value in config_data.items():
                    if hasattr(args, key):
                        setattr(args, key, value)
                    else:
                        print(f"⚠️  Warning: Unknown config key '{key}' in {args.config}")
        else:
            print(f"❌ Config file not found: {args.config}")
            exit(1)

    return args

def print_settings(args):
    print("\nCapture Configuration Summary:")
    print(f"  🧩 Chessboard size       : {args.chessboard_size_column} cols x {args.chessboard_size_row} rows")
    print(f"  📷 Camera name           : {args.camera_name}")
    print(f"  🎥 Resolution            : {args.width} x {args.height}")
    print(f"  💾 Save directory root   : {args.save_dir}")
    print(f"  🎛️  Video device ID       : {args.video_id if args.video_id is not None else 'Auto-detect'}")
    print(f"  📐 Distance threshold    : {PIXEL_DISTANCE_THRESHOLD} pixels\n")

def main():
    args = parse_args()
    print_settings(args)

    camera_name = args.camera_name
    frame_width = args.width
    frame_height = args.height
    chessboard_size = (args.chessboard_size_column, args.chessboard_size_row)
    save_dir_root = args.save_dir

    camera_id = args.video_id if args.video_id is not None else get_external_camera_id()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = os.path.join(save_dir_root, f"{camera_name}_{timestamp}")
    os.makedirs(save_dir, exist_ok=True)

    image_prefix = camera_name
    image_format = "jpg"
    save_centroids = []
    last_saved_centroid = None

    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    if not cap.isOpened():
        print("❌ Cannot open camera")
        exit(1)

    existing_files = [f for f in os.listdir(save_dir) if f.startswith(image_prefix)]
    existing_indices = [int(re.findall(r'\d+', f)[-1]) for f in existing_files if re.findall(r'\d+', f)]
    screenshot_count = max(existing_indices, default=0) + 1

    print("📷 Capturing camera feed. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, chessboard_size)

        if found:
            cv2.drawChessboardCorners(frame, chessboard_size, corners, found)

            centroid = np.mean(corners, axis=0).flatten()
            centroid_int = tuple(int(c) for c in centroid)

            if last_saved_centroid is not None:
                pixel_distance = np.linalg.norm(np.array(centroid) - np.array(last_saved_centroid))
            else:
                pixel_distance = PIXEL_DISTANCE_THRESHOLD + 1

            if pixel_distance > PIXEL_DISTANCE_THRESHOLD:
                filename = f"{image_prefix}_{screenshot_count}.{image_format}"
                filepath = os.path.join(save_dir, filename)
                cv2.imwrite(filepath, frame)
                print(f"✅ Saved image at {pixel_distance:.1f}px movement → {filepath}")
                screenshot_count += 1

                save_centroids.append(centroid_int)
                last_saved_centroid = centroid

        for pt in save_centroids:
            cv2.circle(frame, pt, 4, (0, 0, 255), -1)

        for i in range(1, len(save_centroids)):
            cv2.line(frame, save_centroids[i - 1], save_centroids[i], (255, 0, 0), 2)

        cv2.imshow('Fisheye USB Camera Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()