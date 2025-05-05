"""
Main script for the drone navigation system.
Orchestrates all components and handles the main control loop.
"""

import os
import sys
import time
import logging
import signal
from typing import Optional

from bluetooth_handler import BluetoothHandler
from drone_controller import DroneController
from camera_handler import CameraHandler
from navigation_controller import NavigationController, NavigationPhase
from data_logger import DataLogger

from config import DRONE_CONFIG, VIDEO_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DroneNavigationSystem:
    def __init__(self):
        self.bluetooth = BluetoothHandler()
        self.drone = DroneController()
        self.camera = CameraHandler()
        self.navigation = NavigationController()
        self.data_logger = DataLogger()
        self.is_running = False
        self.real_flight = DRONE_CONFIG["REAL_FLIGHT"]

    def setup(self) -> bool:
        """Set up all system components."""
        try:
            # Setup Bluetooth
            if not self.bluetooth.setup():
                logger.error("Failed to setup Bluetooth")
                return False

            # Wait for Bluetooth connection
            success, client_info = self.bluetooth.wait_for_connection()
            if not success:
                logger.error("No Bluetooth connection established")
                return False

            self.bluetooth.start_listener()
            self.bluetooth.send_message("Connected to program via Bluetooth")

            # Get flight mode
            self.bluetooth.send_message("1: Real Flight  2: No")
            while True:
                msg = self.bluetooth.get_message()
                if msg == "1":
                    self.real_flight = True
                    self.bluetooth.send_message("Doing real flight.")
                    break
                elif msg == "2":
                    self.real_flight = False
                    self.bluetooth.send_message("Not doing real flight.")
                    break

            # Get target height
            self.bluetooth.send_message("Altitude (cm): ")
            while True:
                msg = self.bluetooth.get_message()
                if msg and msg.isdigit():
                    DRONE_CONFIG["TARGET_HEIGHT_CM"] = int(msg)
                    self.bluetooth.send_message(f"Target altitude: {msg}")
                    break

            # Setup drone if real flight
            if self.real_flight:
                if not self.drone.connect():
                    logger.error("Failed to connect to drone")
                    return False

            # Setup camera
            if not self.camera.setup():
                logger.error("Failed to setup camera")
                return False

            # Setup data logger
            if not self.data_logger.setup("navigation_data"):
                logger.error("Failed to setup data logger")
                return False

            logger.info("All components setup successfully")
            return True

        except Exception as e:
            logger.error(f"Error during setup: {e}")
            return False

    def handle_bluetooth_message(self, message: str) -> bool:
        """Handle incoming Bluetooth messages."""
        if message == "stop":
            self.bluetooth.send_message("Initiated STOP command.")
            self.is_running = False
            return True
        elif message == "height" and self.real_flight:
            height = self.drone.get_height()
            self.bluetooth.send_message(f"Height: {height}")
            return True
        return False

    def main_loop(self):
        """Main control loop."""
        try:
            self.is_running = True
            self.bluetooth.send_message("Starting navigation...")

            # Takeoff if real flight
            if self.real_flight:
                if not self.drone.takeoff():
                    logger.error("Failed to takeoff")
                    return

            while self.is_running:
                # Handle Bluetooth messages
                message = self.bluetooth.get_message()
                if message:
                    self.handle_bluetooth_message(message)
                    if not self.is_running:
                        break

                # Read camera frame
                ret, frame = self.camera.read_frame()
                if not ret:
                    logger.warning("Failed to read frame")
                    continue

                # Detect markers
                markers, frame = self.camera.detect_markers(frame)

                # Get current height
                current_height = self.drone.get_height() if self.real_flight else DRONE_CONFIG["TARGET_HEIGHT_CM"]

                # Update navigation state
                self.navigation.update_state(markers, current_height, DRONE_CONFIG["TARGET_HEIGHT_CM"])

                # Get target marker
                target_marker = next((m for m in markers if m.id == self.navigation.state.target_id), None)

                # Calculate control values
                control_values = self.navigation.calculate_control(
                    target_marker, current_height, DRONE_CONFIG["TARGET_HEIGHT_CM"]
                )

                # Send control commands to drone
                if self.real_flight:
                    self.drone.send_rc_control(
                        control_values["left_right"],
                        control_values["forward_backward"],
                        control_values["up_down"],
                        control_values["yaw"]
                    )

                # Log data
                self.data_logger.log_data(
                    self.navigation.state.phase.value,
                    self.navigation.state.target_id,
                    self.navigation.state.reached_id,
                    current_height,
                    DRONE_CONFIG["TARGET_HEIGHT_CM"],
                    target_marker.center_x if target_marker else None,
                    target_marker.center_y if target_marker else None,
                    target_marker.distance if target_marker else None,
                    control_values
                )

                # Draw overlay
                frame = self.camera.draw_overlay(
                    frame, markers,
                    self.navigation.state.target_id,
                    self.navigation.state.reached_id,
                    current_height,
                    control_values
                )

                # Write frame to video
                self.camera.write_frame(frame)

                # Check for landing condition
                if self.navigation.state.phase == NavigationPhase.LANDING:
                    self.bluetooth.send_message("Landing marker reached. Landing...")
                    break

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up all system components."""
        try:
            # Stop drone
            if self.real_flight:
                self.drone.emergency_stop()
                self.drone.cleanup()

            # Clean up other components
            self.camera.cleanup()
            self.data_logger.cleanup()
            self.bluetooth.cleanup()

            logger.info("System cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def signal_handler(signum, frame):
    """Handle system signals."""
    logger.info("Received signal to terminate")
    if hasattr(signal_handler, 'system'):
        signal_handler.system.cleanup()
    sys.exit(0)

def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run system
    system = DroneNavigationSystem()
    signal_handler.system = system

    if system.setup():
        system.main_loop()
    else:
        logger.error("System setup failed")
        system.cleanup()

if __name__ == "__main__":
    main() 