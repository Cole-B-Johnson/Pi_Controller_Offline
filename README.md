# System Documentation

## Overview
The provided system comprises two main Python scripts, `vfd_control.py` and `sensor_suite.py`, which are executed in the background upon launching the `launch.sh` shell script. This system is designed to interact with Variable Frequency Drives (VFDs) and various sensors connected to the system.

## Directory Structure
Below is the directory structure depicting the layout of files and directories:

```
/
├── home/
│   └── levitree/
│       └── Desktop/
│           ├── Pi_Controller_Offline/
│           │   ├── vfd_control.py
│           │   └── sensor_suite.py
│           └── Live-Data-Pathways/
│               ├── Hydrapulper/
│               │   ├── To_VFD/
│               │   └── From_VFD/
│               ├── 3_Progressive_Cavity_Pump/
│               │   ├── To_VFD/
│               │   └── From_VFD/
│               ├── 4_Progressive_Cavity_Pump/
│               │   ├── To_VFD/
│               │   └── From_VFD/
│               └── Auger_Truck/
│                   ├── To_VFD/
│                   └── From_VFD/
└── logs/
    ├── sensor_data_{timestamp}.log
    └── vfd_control_{timestamp}.log
```

## System Components

### Scripts
#### 1. `vfd_control.py`:
   - **Purpose**: Controls and interacts with Variable Frequency Drives (VFDs).
   - **Logging**: Generates a timestamped log file `vfd_control_{timestamp}.log` in the `/logs` directory for VFD control-related logging.
   
#### 2. `sensor_suite.py`:
   - **Purpose**: Collects and processes data from distance and pressure sensors connected to the system.
   - **Logging**: Generates a timestamped log file `sensor_data_{timestamp}.log` in the `/logs` directory for sensor-related logging.
   
### Shell Script: `launch.sh`
- **Purpose**: Initiates the `vfd_control.py` and `sensor_suite.py` scripts.
- **Execution Instructions**: Run the script in a terminal. It will start both Python scripts in the background, initializing the VFD Control System and Sensor Suite.

## Execution Workflow

1. **VFD Control Initialization**: The `vfd_control.py` script is executed with a specified port argument. It initializes the VFD control system and starts interacting with the connected VFD devices.

2. **Sensor Suite Initialization**: The `sensor_suite.py` script is executed with specified port arguments and a directory path. It initializes the sensor suite, collecting and processing data from distance and pressure sensors.

## Usage
Run `launch.sh` to start the system:

```bash
./launch.sh
```
Ensure you have the necessary permissions to execute the script.

## Notes for Users
- The system continuously collects, processes, and logs data until manually interrupted.
- Data sent to VFDs and data received from VFDs are stored in respective `To_VFD/` and `From_VFD/` subdirectories under each device's named directory in `Live-Data-Pathways/`.
- Consult the generated log files in the `/logs` directory for monitoring system behavior and troubleshooting.

## Important
Before deploying the system, ensure the target environment is properly configured, and directories exist with appropriate permissions. Test the system in a controlled environment before full-scale deployment. Always have a backup of crucial data to prevent loss during system operation.
