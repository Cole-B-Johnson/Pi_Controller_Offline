import os
import time
import argparse
import shutil
import json
import RPi.GPIO as GPIO
import Adafruit_ADS1x15

def dist():
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
    TimeElapsed = StopTime - StartTime
    distance = (TimeElapsed * 34300) / 2
    return distance

def save_to_directory(directory_path, data):
    file_name = f'sensor_data_{int(time.time())}.json'
    file_path_pressure = os.path.join(directory_path, 'Pump_Pressure', file_name)
    file_path_distance = os.path.join(directory_path, 'Depth_Sensor', file_name)
    try:
        with open(file_path_distance, 'w') as f:
            json.dump(data['distance_sensor'], f)
    except Exception as e:
        print(f"Error writing to file {file_path_distance}: {e}")
    try:
        with open(file_path_pressure, 'w') as f:
            json.dump(data['pressure_sensor'], f)
    except Exception as e:
        print(f"Error writing to file {file_path_pressure}: {e}")

def print_and_save_sensor_data(dis, pressure, directory_path):
    # print(f"Mix Tank Distance {dis} mm")
    # print(f"Pressure Sensor Reading: {pressure}")
    
    data = {'distance_sensor': dis, 'pressure_sensor': pressure}
    save_to_directory(directory_path, data)

def clear_directory(directory_path):
    for folder in ['Pump_Pressure', 'Depth_Sensor']:
        folder_path = os.path.join(directory_path, folder)
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port1', required=True, help='The port for the distance sensor connection')
    parser.add_argument('--port2', required=True, help='The port for the pressure sensor connection') # 0x48
    parser.add_argument('--directory', required=True, help='The directory to save the sensor data')
    args = parser.parse_args()

    # Pressure Sensor
    adc = Adafruit_ADS1x15.ADS1115(address=int(args.port2, 16))
    GAIN = 1

    # Distance Sensor
    GPIO.setmode(GPIO.BCM)
    GPIO_TRIGGER = 18
    GPIO_ECHO = 24
    GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
    GPIO.setup(GPIO_ECHO, GPIO.IN)
    
    # Directory path
    directory_path = args.directory
    print(f'Sensor Suite -- Clearing Directory')
    clear_directory(directory_path)
    delay_time = .1
    print('Sensor Suite -- Initialization Complete')
    try:
        while True:
            distance = dist()
            adc_reading = adc.read_adc(3, gain=GAIN)
            pressure = .004686267155 * adc_reading - 19.09735 # relation for 5v and 150psi sensor
            print_and_save_sensor_data(distance, pressure, directory_path)
            time.sleep(delay_time)
    except KeyboardInterrupt:
        print(f'CTRL + C -- Measured data saved to {directory_path}')
        GPIO.cleanup()
