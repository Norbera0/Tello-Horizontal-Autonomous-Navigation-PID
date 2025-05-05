"""
Configuration parameters for the drone navigation system.
All parameters are organized into logical sections for better maintainability.
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"
VIDEO_OUTPUT_DIR = OUTPUT_DIR / "videos"
CSV_OUTPUT_DIR = OUTPUT_DIR / "csv"

# Create output directories if they don't exist
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

# Drone configuration
DRONE_CONFIG = {
    "SPEED_SCALE": 0.4,
    "TARGET_HEIGHT_CM": 150,
    "HEADLESS_MODE": False,
    "REAL_FLIGHT": False,
}

# Video configuration
VIDEO_CONFIG = {
    "WIDTH": 320,
    "HEIGHT": 240,
    "FPS": 12,
    "CODEC": "XVID",
}

# Camera configuration
CAMERA_CONFIG = {
    "DEVICE_ID": 0,
    "FPS": 12,
    "WIDTH": 320,
    "HEIGHT": 240,
}

# ArUco configuration
ARUCO_CONFIG = {
    "DICT_TYPE": "DICT_4X4_250",
    "THRESHOLD": 25,
    "TARGET_X": 160,  # VIDEO_CONFIG["WIDTH"] / 2
    "TARGET_Y": 192,  # VIDEO_CONFIG["HEIGHT"] * 0.8
}

# PID configuration
PID_CONFIG = {
    "X": {
        "KP": 1.5,
        "KI": 0.1,
        "KD": 0.15,
    },
    "Y": {
        "KP": 1.0,
        "KI": 0.1,
        "KD": 0.15,
    },
    "R": {
        "KP": 0.8,
        "KI": 0.0,
        "KD": 0.0,
    },
}

# Bluetooth configuration
BLUETOOTH_CONFIG = {
    "PORT": 1,
    "TIMEOUT_SEC": 60,
}

# WiFi configuration
WIFI_CONFIG = {
    "SSID": "TELLO-F27208",
    "MAX_CONNECT_ATTEMPTS": 10,
    "CONNECT_TIMEOUT_SEC": 5,
}

# Navigation configuration
NAVIGATION_CONFIG = {
    "MAX_ID_TIME_RESET": 5,
    "TARGET_LOST_TIMEOUT_SEC": 3,
    "ROTATION_SPEED": 50,
    "HEIGHT_TOLERANCE_CM": 4,
}

# Output configuration
OUTPUT_CONFIG = {
    "VIDEO_FILENAME": "output_video.mp4",
    "CSV_FILENAME": "position_data.csv",
} 