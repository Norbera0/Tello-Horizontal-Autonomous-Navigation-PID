"""
Data logger module for recording navigation data to CSV files.
Handles data collection, formatting, and file I/O operations.
"""

import csv
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

from config import CSV_OUTPUT_DIR

logger = logging.getLogger(__name__)

class DataLogger:
    def __init__(self):
        self.csv_file: Optional[csv.writer] = None
        self.csv_path: Optional[Path] = None
        self.start_time = time.time()
        self.data_buffer: List[Dict] = []

    def setup(self, filename: str) -> bool:
        """Set up CSV file for data logging."""
        try:
            # Create output directory if it doesn't exist
            CSV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # Create CSV file with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.csv_path = CSV_OUTPUT_DIR / f"{filename}_{timestamp}.csv"

            # Initialize CSV writer
            csv_file = open(self.csv_path, 'w', newline='')
            self.csv_file = csv.writer(csv_file)

            # Write header
            self.csv_file.writerow([
                'timestamp',
                'phase',
                'target_id',
                'reached_id',
                'current_height',
                'target_height',
                'marker_x',
                'marker_y',
                'marker_distance',
                'control_x',
                'control_y',
                'control_z',
                'control_yaw'
            ])

            logger.info(f"Data logging initialized: {self.csv_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup data logger: {e}")
            return False

    def log_data(self, phase: int, target_id: int, reached_id: int,
                 current_height: float, target_height: float,
                 marker_x: Optional[float], marker_y: Optional[float],
                 marker_distance: Optional[float],
                 control_values: Dict[str, int]) -> bool:
        """Log navigation data to CSV."""
        try:
            if self.csv_file is None:
                return False

            # Prepare data row
            data = {
                'timestamp': time.time() - self.start_time,
                'phase': phase,
                'target_id': target_id,
                'reached_id': reached_id,
                'current_height': current_height,
                'target_height': target_height,
                'marker_x': marker_x if marker_x is not None else 0,
                'marker_y': marker_y if marker_y is not None else 0,
                'marker_distance': marker_distance if marker_distance is not None else 0,
                'control_x': control_values['left_right'],
                'control_y': control_values['forward_backward'],
                'control_z': control_values['up_down'],
                'control_yaw': control_values['yaw']
            }

            # Write data row
            self.csv_file.writerow(data.values())
            self.data_buffer.append(data)

            return True

        except Exception as e:
            logger.error(f"Error logging data: {e}")
            return False

    def get_statistics(self) -> Dict[str, float]:
        """Calculate and return navigation statistics."""
        try:
            if not self.data_buffer:
                return {}

            # Convert buffer to numpy array for calculations
            data = np.array([list(d.values()) for d in self.data_buffer])

            # Calculate statistics
            stats = {
                'total_time': data[-1, 0] - data[0, 0],  # Last timestamp - first timestamp
                'avg_height_error': np.mean(np.abs(data[:, 4] - data[:, 5])),  # Current height - target height
                'avg_marker_distance': np.mean(data[:, 8]),  # Average marker distance
                'max_control_x': np.max(np.abs(data[:, 9])),  # Maximum X control
                'max_control_y': np.max(np.abs(data[:, 10])),  # Maximum Y control
                'max_control_z': np.max(np.abs(data[:, 11])),  # Maximum Z control
                'max_control_yaw': np.max(np.abs(data[:, 12]))  # Maximum yaw control
            }

            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    def cleanup(self):
        """Clean up data logger resources."""
        try:
            if self.csv_file is not None:
                self.csv_file.writer.writerow([])  # Add empty line
                self.csv_file.writer.writerow(['Statistics:'])
                
                # Write statistics
                stats = self.get_statistics()
                for key, value in stats.items():
                    self.csv_file.writerow([key, f"{value:.4f}"])

                self.csv_file.writer.writer.writerow([])  # Add empty line
                self.csv_file.writer.writerow(['End of log'])
                self.csv_file.writer.writer.close()

            logger.info("Data logger cleanup complete")

        except Exception as e:
            logger.error(f"Error during data logger cleanup: {e}") 