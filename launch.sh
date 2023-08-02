#!/bin/bash

python3 /home/levitree/Desktop/Pi_Controller_Offline/vfd_control.py --port '/dev/ttyUSB0' &
echo "VFD Control System Initialized..."

python3 /home/levitree/Desktop/Pi_Controller_Offline/sensor_suite.py --port1 '/dev/ttyAMA0' --port2 '0x48' --directory '/home/levitree/Desktop/Live-Data-Pathways' &
echo "Sensor Suite Initialized..."