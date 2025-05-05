"""
Camera handler module for video capture and ArUco marker detection.
Manages camera setup, frame capture, and marker detection functionality.
"""

import cv2
import cv2.aruco as aruco
import numpy as np
import logging
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

from config import CAMERA_CONFIG, ARUCO_CONFIG, VIDEO_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class MarkerInfo:
    """Data class for storing marker detection information."""
    id: int
    corners: np.ndarray
    center_x: float
    center_y: float
    distance: float

class CameraHandler:
    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.aruco_dict = None
        self.aruco_params = None
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.frame_count = 0
        self.start_time = 0

    def setup(self) -> bool:
        """Set up camera and ArUco detection."""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(CAMERA_CONFIG["DEVICE_ID"])
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_CONFIG["FPS"])
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CONFIG["WIDTH"])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CONFIG["HEIGHT"])

            if not self.cap.isOpened():
                logger.error("Failed to open camera")
                return False

            # Initialize ArUco detection
            self.aruco_dict = aruco.Dictionary_get(getattr(aruco, ARUCO_CONFIG["DICT_TYPE"]))
            self.aruco_params = aruco.DetectorParameters_create()

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_CONFIG["CODEC"])
            self.video_writer = cv2.VideoWriter(
                str(VIDEO_CONFIG["OUTPUT_PATH"]),
                fourcc,
                VIDEO_CONFIG["FPS"],
                (CAMERA_CONFIG["WIDTH"], CAMERA_CONFIG["HEIGHT"])
            )

            self.start_time = cv2.getTickCount()
            logger.info("Camera and ArUco detection setup successful")
            return True

        except Exception as e:
            logger.error(f"Failed to setup camera: {e}")
            return False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame from the camera."""
        if self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Failed to read frame from camera")
            return False, None

        self.frame_count += 1
        return True, frame

    def detect_markers(self, frame: np.ndarray) -> Tuple[List[MarkerInfo], np.ndarray]:
        """Detect ArUco markers in the frame."""
        if frame is None:
            return [], frame

        try:
            # Detect markers
            corners, ids, rejected = aruco.detectMarkers(
                frame, self.aruco_dict, parameters=self.aruco_params
            )

            # Process detected markers
            markers = []
            if ids is not None:
                for i, marker_id in enumerate(ids):
                    marker_corners = corners[i][0]
                    
                    # Calculate center point
                    center_x = np.mean(marker_corners[:, 0])
                    center_y = np.mean(marker_corners[:, 1])
                    
                    # Calculate distance from target point
                    dx = center_x - ARUCO_CONFIG["TARGET_X"]
                    dy = center_y - ARUCO_CONFIG["TARGET_Y"]
                    distance = np.sqrt(dx*dx + dy*dy)

                    markers.append(MarkerInfo(
                        id=int(marker_id[0]),
                        corners=marker_corners,
                        center_x=center_x,
                        center_y=center_y,
                        distance=distance
                    ))

                # Draw detected markers
                frame = aruco.drawDetectedMarkers(frame, corners, ids)

            return markers, frame

        except Exception as e:
            logger.error(f"Error in marker detection: {e}")
            return [], frame

    def draw_overlay(self, frame: np.ndarray, markers: List[MarkerInfo], 
                    target_id: int, reached_id: int, height: float,
                    control_values: Dict[str, int]) -> np.ndarray:
        """Draw overlay information on the frame."""
        if frame is None:
            return frame

        try:
            # Draw target area
            topleft = (int(ARUCO_CONFIG["TARGET_X"] - ARUCO_CONFIG["THRESHOLD"]),
                      int(ARUCO_CONFIG["TARGET_Y"] - ARUCO_CONFIG["THRESHOLD"]))
            bottomright = (int(ARUCO_CONFIG["TARGET_X"] + ARUCO_CONFIG["THRESHOLD"]),
                         int(ARUCO_CONFIG["TARGET_Y"] + ARUCO_CONFIG["THRESHOLD"]))
            cv2.rectangle(frame, topleft, bottomright, (0, 0, 255), 2)

            # Draw text information
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, f"Target ID: {target_id}", (25, 25), font, 0.75, (0, 255, 0), 2)
            cv2.putText(frame, f"Reached ID: {reached_id}", (25, 50), font, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Height: {height/100:.1f}m", (25, 75), font, 0.5, (0, 255, 0), 2)

            # Draw control values
            cv2.putText(frame, f"X: {control_values['left_right']}", (10, frame.shape[0]-60), font, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Y: {control_values['forward_backward']}", (10, frame.shape[0]-45), font, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"R: {control_values['yaw']}", (10, frame.shape[0]-30), font, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Z: {control_values['up_down']}", (10, frame.shape[0]-15), font, 0.5, (0, 255, 0), 2)

            return frame

        except Exception as e:
            logger.error(f"Error drawing overlay: {e}")
            return frame

    def write_frame(self, frame: np.ndarray) -> bool:
        """Write frame to video file."""
        if self.video_writer is None or frame is None:
            return False

        try:
            self.video_writer.write(frame)
            return True
        except Exception as e:
            logger.error(f"Error writing frame to video: {e}")
            return False

    def get_fps(self) -> float:
        """Calculate current FPS."""
        if self.frame_count == 0:
            return 0.0

        elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
        return self.frame_count / elapsed_time if elapsed_time > 0 else 0.0

    def cleanup(self):
        """Clean up camera and video resources."""
        if self.cap is not None:
            self.cap.release()

        if self.video_writer is not None:
            self.video_writer.release()

        cv2.destroyAllWindows()
        logger.info("Camera resources cleaned up") 