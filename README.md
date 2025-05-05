# Tello-Horizontal-Autonomous-Navigation-PID

An autonomous drone navigation system using ArUco markers and PID control, implemented on a Raspberry Pi Zero 2W.

## Overview

This project enables a Ryze Tello drone to autonomously navigate through a series of ArUco markers while maintaining a specified altitude. The system uses computer vision for marker detection and PID control for smooth movement.

<div style="display: flex;">
  <img src="Documentations/SetupDrone1.jpg" alt="Setup 1" style="width: 45%; margin-right: 5%;"/>
  <img src="Documentations/SetupDrone2.jpg" alt="Setup 2" style="width: 45%;"/>
</div>

## Features

- Real-time ArUco marker detection using OpenCV
- PID control for smooth drone movement
- Bluetooth communication for remote control and monitoring
- Data logging for performance analysis
- Video recording of navigation
- Support for both real flight and simulation modes

## Hardware Requirements

- Raspberry Pi Zero 2W
- Pi Camera Module V2
- Ryze Tello Drone
- External battery for RPi (5V)
- Power module for voltage regulation
- Bluetooth-capable phone for control

## Software Requirements

- Raspberry Pi OS (Bullseye or newer)
- Python 3.7+
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Drone-Aruco-PID-Autonavigate.git
   cd Drone-Aruco-PID-Autonavigate
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Enable the camera on your Raspberry Pi:
   ```bash
   sudo raspi-config
   # Navigate to Interface Options > Camera and enable it
   ```

5. Configure Bluetooth:
   ```bash
   sudo apt-get install bluetooth bluez
   sudo usermod -a -G bluetooth $USER
   ```

## Configuration

The system is configured through `config.py`. Key parameters include:

- `DRONE_CONFIG`: Flight parameters (speed scale, target height)
- `PID_CONFIG`: PID controller gains for X, Y, and rotation
- `ARUCO_CONFIG`: Marker detection settings
- `VIDEO_CONFIG`: Camera and video recording settings
- `BLUETOOTH_CONFIG`: Bluetooth communication settings

## Usage

1. Start the program:
   ```bash
   python src/main.py
   ```

2. Connect to the RPi via Bluetooth using a terminal app on your phone.

3. Follow the on-screen prompts to:
   - Choose between real flight or simulation mode
   - Set the target altitude
   - Start/stop navigation

4. The drone will:
   - Take off to the specified height
   - Detect and navigate to ArUco markers in sequence
   - Land when it reaches the final marker (ID 0)

## Project Structure

```
Tello-Horizontal-Autonomous-Navigation-PID/
├── src/
│   ├── main.py              # Main program entry point
│   ├── bluetooth_handler.py # Bluetooth communication
│   ├── camera_handler.py    # Camera and ArUco detection
│   ├── drone_controller.py  # Drone control interface
│   ├── navigation_controller.py # Navigation and PID control
│   └── data_logger.py       # Data logging and analysis
├── config.py                # Configuration parameters
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── Documentations/         # Documentation and media
```

## Output Files

- **Video**: Recorded in `output/videos/` with timestamp
- **Data**: CSV files in `output/csv/` containing:
  - Timestamp
  - Navigation phase
  - Target and reached marker IDs
  - Height measurements
  - Marker positions
  - Control values
  - Performance statistics

## Flight Samples

Two samples of actual flight as seen from the pi cam can be accessed [here](https://github.com/mangabaycjake/Drone-Aruco-PID-Autonavigate/tree/main/Documentations).

<div style="display: flex;">
  <img src="Documentations/output_video_19.725_0.0832.gif" alt="Flight 1" style="width: 100%; margin-right: 10%;"/>
  <img src="Documentations/output_video_20.882_0.0832.gif" alt="Flight 2" style="width: 100%;"/>
</div>

## Safety Features

- Emergency stop via Bluetooth command
- Automatic landing on connection loss
- Height maintenance with tolerance checks
- Signal handling for graceful shutdown
- Comprehensive error logging

## Troubleshooting

1. **Camera Issues**:
   - Check camera connection
   - Verify camera is enabled in `raspi-config`
   - Test with `raspistill -o test.jpg`

2. **Bluetooth Issues**:
   - Ensure Bluetooth is enabled
   - Check device pairing
   - Verify user is in the bluetooth group

3. **Drone Connection**:
   - Verify WiFi connection to Tello
   - Check battery level
   - Ensure clear line of sight

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Hardware setup inspired by [erviveksoni's post](https://github.com/erviveksoni/raspberrypi-controlled-tello)
- ArUco marker detection using OpenCV
- PID control implementation using simple-pid


