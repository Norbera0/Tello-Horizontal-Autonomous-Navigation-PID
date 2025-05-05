"""
Drone controller module for handling Tello drone operations.
Wraps the djitellopy functionality with additional error handling and safety features.
"""

import os
import time
import logging
from typing import Optional, Tuple
from djitellopy import Tello

from config import DRONE_CONFIG, WIFI_CONFIG

logger = logging.getLogger(__name__)

class DroneController:
    def __init__(self):
        self.drone: Optional[Tello] = None
        self.is_flying = False
        self.is_connected = False
        self.current_height = 0

    def connect(self) -> bool:
        """Connect to the Tello drone via WiFi."""
        try:
            # Disconnect from any existing WiFi
            os.system("sudo wpa_cli disconnect")
            time.sleep(1)

            # Connect to Tello WiFi
            error_count = 0
            while error_count < WIFI_CONFIG["MAX_CONNECT_ATTEMPTS"]:
                logger.info(f"Attempting to connect to {WIFI_CONFIG['SSID']}...")
                os.system(f"sudo nmcli d wifi connect '{WIFI_CONFIG['SSID']}'")
                time.sleep(WIFI_CONFIG["CONNECT_TIMEOUT_SEC"])

                # Check if connected
                if self._check_wifi_connection(WIFI_CONFIG["SSID"]):
                    logger.info("Successfully connected to Tello WiFi")
                    break

                error_count += 1
                logger.warning(f"Failed to connect to Tello WiFi (attempt {error_count})")

            if error_count >= WIFI_CONFIG["MAX_CONNECT_ATTEMPTS"]:
                logger.error("Failed to connect to Tello WiFi after maximum attempts")
                return False

            # Initialize Tello connection
            self.drone = Tello()
            self.drone.connect()
            self.is_connected = True

            # Get initial battery level
            battery = self.drone.get_battery()
            logger.info(f"Drone connected. Battery level: {battery}%")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to drone: {e}")
            return False

    def _check_wifi_connection(self, ssid: str) -> bool:
        """Check if connected to specified WiFi network."""
        cmd = f"iwgetid | grep -o '{ssid}'"
        return os.system(cmd) == 0

    def takeoff(self) -> bool:
        """Execute drone takeoff with safety checks."""
        if not self.is_connected or self.drone is None:
            logger.error("Cannot takeoff: Drone not connected")
            return False

        try:
            self.drone.takeoff()
            self.is_flying = True
            logger.info("Drone takeoff successful")
            return True
        except Exception as e:
            logger.error(f"Takeoff failed: {e}")
            return False

    def land(self) -> bool:
        """Execute drone landing with safety checks."""
        if not self.is_connected or self.drone is None:
            logger.error("Cannot land: Drone not connected")
            return False

        try:
            self.drone.land()
            self.is_flying = False
            logger.info("Drone landing successful")
            return True
        except Exception as e:
            logger.error(f"Landing failed: {e}")
            return False

    def send_rc_control(self, left_right: int, forward_backward: int, up_down: int, yaw: int) -> bool:
        """Send RC control commands to the drone with safety checks."""
        if not self.is_connected or self.drone is None:
            logger.error("Cannot send RC control: Drone not connected")
            return False

        try:
            # Scale the control values
            scale = DRONE_CONFIG["SPEED_SCALE"]
            left_right = int(left_right * scale)
            forward_backward = int(forward_backward * scale)
            up_down = int(up_down * scale)
            yaw = int(yaw * scale)

            self.drone.send_rc_control(left_right, forward_backward, up_down, yaw)
            return True
        except Exception as e:
            logger.error(f"Failed to send RC control: {e}")
            return False

    def get_height(self) -> int:
        """Get current drone height in centimeters."""
        if not self.is_connected or self.drone is None:
            return 0

        try:
            self.current_height = self.drone.get_height()
            return self.current_height
        except Exception as e:
            logger.error(f"Failed to get drone height: {e}")
            return self.current_height

    def get_battery(self) -> int:
        """Get current drone battery percentage."""
        if not self.is_connected or self.drone is None:
            return 0

        try:
            return self.drone.get_battery()
        except Exception as e:
            logger.error(f"Failed to get battery level: {e}")
            return 0

    def emergency_stop(self):
        """Emergency stop procedure."""
        if self.is_connected and self.drone is not None:
            try:
                self.drone.send_rc_control(0, 0, 0, 0)
                if self.is_flying:
                    self.land()
            except:
                pass

    def cleanup(self):
        """Clean up drone resources."""
        if self.is_connected and self.drone is not None:
            try:
                if self.is_flying:
                    self.land()
                self.drone.end()
            except:
                pass
        self.is_connected = False
        self.is_flying = False
        logger.info("Drone resources cleaned up") 