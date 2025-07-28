FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    v4l-utils \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    python3-tk && \
  # Clean up package caches and remove unnecessary files
  rm -rf /var/lib/apt/lists/* && \
  apt-get clean

RUN pip install --no-cache-dir \
  click \
  cycler \
  fonttools \
  kiwisolver \
  matplotlib \
  numpy \
  opencv-python \
  packaging \
  Pillow \
  pyparsing \
  python-dateutil \
  scipy \
  six \
  tqdm \
  typer \
  setuptools \
  loguru \
  pyqtgraph \
  PyQt5 \
  pyyaml

COPY calibration_routine.sh /calibration_routine.sh
COPY camera_calib_capture.py /camera_calib_capture.py