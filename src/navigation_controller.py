"""
Navigation controller module for handling drone navigation and PID control.
Manages navigation state, PID controllers, and control calculations.
"""

import time
import logging
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple
from simple_pid import PID

from config import PID_CONFIG, NAVIGATION_CONFIG, ARUCO_CONFIG

logger = logging.getLogger(__name__)

class NavigationPhase(Enum):
    """Enumeration of navigation phases."""
    TAKEOFF = 0
    ALIGNING = 1
    APPROACHING = 2
    LANDING = 3

@dataclass
class NavigationState:
    """Data class for storing navigation state."""
    phase: NavigationPhase
    target_id: int
    reached_id: int
    max_id: int
    last_target_time: float
    last_max_id_time: float

class NavigationController:
    def __init__(self):
        # Initialize PID controllers
        self.pid_x = PID(
            Kp=PID_CONFIG["X"]["KP"],
            Ki=PID_CONFIG["X"]["KI"],
            Kd=PID_CONFIG["X"]["KD"],
            setpoint=0
        )
        self.pid_y = PID(
            Kp=PID_CONFIG["Y"]["KP"],
            Ki=PID_CONFIG["Y"]["KI"],
            Kd=PID_CONFIG["Y"]["KD"],
            setpoint=0
        )
        self.pid_r = PID(
            Kp=PID_CONFIG["R"]["KP"],
            Ki=PID_CONFIG["R"]["KI"],
            Kd=PID_CONFIG["R"]["KD"],
            setpoint=0
        )

        # Initialize navigation state
        self.state = NavigationState(
            phase=NavigationPhase.TAKEOFF,
            target_id=1,
            reached_id=0,
            max_id=0,
            last_target_time=time.time(),
            last_max_id_time=time.time()
        )

        # Initialize control values
        self.control_values = {
            "left_right": 0,
            "forward_backward": 0,
            "up_down": 0,
            "yaw": 0
        }

    def update_state(self, markers: list, current_height: float, target_height: float) -> bool:
        """Update navigation state based on detected markers and current height."""
        try:
            current_time = time.time()

            # Update max_id if new markers are detected
            if markers:
                max_marker_id = max(marker.id for marker in markers)
                if max_marker_id > self.state.max_id:
                    self.state.max_id = max_marker_id
                    self.state.last_max_id_time = current_time

            # Check for target marker
            target_marker = next((m for m in markers if m.id == self.state.target_id), None)
            if target_marker:
                self.state.last_target_time = current_time

            # Handle navigation phases
            if self.state.phase == NavigationPhase.TAKEOFF:
                if abs(current_height - target_height) <= NAVIGATION_CONFIG["HEIGHT_TOLERANCE_CM"]:
                    self.state.phase = NavigationPhase.ALIGNING
                    logger.info("Takeoff complete, starting alignment phase")

            elif self.state.phase == NavigationPhase.ALIGNING:
                if target_marker and target_marker.distance <= ARUCO_CONFIG["THRESHOLD"]:
                    self.state.phase = NavigationPhase.APPROACHING
                    logger.info("Alignment complete, starting approach phase")

            elif self.state.phase == NavigationPhase.APPROACHING:
                if target_marker and target_marker.distance <= ARUCO_CONFIG["THRESHOLD"]:
                    if self.state.target_id == 0:  # Landing marker
                        self.state.phase = NavigationPhase.LANDING
                        logger.info("Landing marker reached, starting landing phase")
                    else:
                        self.state.reached_id += 1
                        self.state.target_id += 1
                        logger.info(f"Reached marker {self.state.reached_id}, targeting {self.state.target_id}")

            return True

        except Exception as e:
            logger.error(f"Error updating navigation state: {e}")
            return False

    def calculate_control(self, target_marker: Optional[object], current_height: float, 
                         target_height: float) -> Dict[str, int]:
        """Calculate control values based on current state and target marker."""
        try:
            # Reset control values
            self.control_values = {k: 0 for k in self.control_values}

            # Handle height control
            if current_height > target_height + NAVIGATION_CONFIG["HEIGHT_TOLERANCE_CM"]:
                self.control_values["up_down"] = -20
            elif current_height < target_height - NAVIGATION_CONFIG["HEIGHT_TOLERANCE_CM"]:
                self.control_values["up_down"] = 20

            # Handle marker-based control
            if target_marker:
                # Calculate normalized position errors
                dx = (target_marker.center_x - ARUCO_CONFIG["TARGET_X"]) / ARUCO_CONFIG["TARGET_X"]
                dy = (ARUCO_CONFIG["TARGET_Y"] - target_marker.center_y) / ARUCO_CONFIG["TARGET_Y"]

                # Calculate rotation error
                if dx != 0:
                    try:
                        rotation_error = np.arctan(dx/dy) * 180 / np.pi
                    except:
                        rotation_error = 0
                else:
                    rotation_error = 0

                # Calculate PID outputs
                if self.state.phase == NavigationPhase.ALIGNING:
                    # Use rotation control for alignment
                    self.control_values["yaw"] = int(self.pid_r(-rotation_error))
                else:
                    # Use position control for approach
                    self.control_values["left_right"] = int(self.pid_x(-dx * 100))
                    self.control_values["forward_backward"] = int(self.pid_y(-dy * 100))

            # Clamp control values
            for key in self.control_values:
                self.control_values[key] = max(min(self.control_values[key], 100), -100)

            return self.control_values

        except Exception as e:
            logger.error(f"Error calculating control values: {e}")
            return {k: 0 for k in self.control_values}

    def reset_pid(self):
        """Reset all PID controllers."""
        self.pid_x.reset()
        self.pid_y.reset()
        self.pid_r.reset()

    def is_target_lost(self) -> bool:
        """Check if target marker has been lost for too long."""
        return (time.time() - self.state.last_target_time) > NAVIGATION_CONFIG["TARGET_LOST_TIMEOUT_SEC"]

    def should_update_max_id(self) -> bool:
        """Check if max_id should be updated based on timeout."""
        return (time.time() - self.state.last_max_id_time) > NAVIGATION_CONFIG["MAX_ID_TIME_RESET"] 