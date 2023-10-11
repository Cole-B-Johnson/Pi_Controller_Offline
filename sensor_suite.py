import os
import time
import argparse
import shutil
import json
import RPi.GPIO as GPIO
import Adafruit_ADS1x15
import logging
import datetime

# Set up logger
log_directory = "/home/levitree/Desktop/logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)  # Creates the directory if it does not exist

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Generates a string with the current date and time
log_file_name = f"sensor_data_{current_time}.log"  # Appends the timestamp to the logfile's name
log_file_path = os.path.join(log_directory, log_file_name)  # Joins the directory with the new logfile name

logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def dist():
    try:
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

        if not isinstance(distance, (int, float)):
            error_msg = "Error: Calculated distance is not a number"
            # print(error_msg)
            logger.error(error_msg)
            return None
        return distance
    except Exception as e:
        error_msg = f"Error calculating distance: {e}"
        # print(error_msg)
        logger.error(error_msg)
        return None

def save_to_directory(directory_path, data):
    if not data['distance_sensor'] or not data['pressure_sensor']:
        error_msg = "Error: Missing sensor data"
        # print(error_msg)
        logger.error(error_msg)
        return

    file_name = f'sensor_data_{int(time.time())}.json'
    file_path_pressure = os.path.join(directory_path, 'Pump_Pressure', file_name)
    file_path_distance = os.path.join(directory_path, 'Depth_Sensor', file_name)

    try:
        os.makedirs(os.path.dirname(file_path_distance), exist_ok=True)
        with open(file_path_distance, 'w') as f:
            json.dump(data['distance_sensor'], f)
    except Exception as e:
        error_msg = f"Error writing to file {file_path_distance}: {e}"
        # print(error_msg)
        logger.error(error_msg)

    try:
        os.makedirs(os.path.dirname(file_path_pressure), exist_ok=True)
        with open(file_path_pressure, 'w') as f:
            json.dump(data['pressure_sensor'], f)
    except Exception as e:
        error_msg = f"Error writing to file {file_path_pressure}: {e}"
        # print(error_msg)
        logger.error(error_msg)

def print_and_save_sensor_data(dis, pressure, directory_path):
    if dis is not None and pressure is not None:
        info_msg1 = f"Mix Tank Distance {dis} mm"
        info_msg2 = f"Pressure Sensor Reading: {pressure}"
        print(info_msg1)
        print(info_msg2)
        logger.info(info_msg1)
        logger.info(info_msg2)

        data = {'distance_sensor': dis, 'pressure_sensor': pressure}
        save_to_directory(directory_path, data)
    else:
        error_msg = "Error: Invalid sensor data"
        # print(error_msg)
        logger.error(error_msg)

def clear_directory(directory_path):
    for folder in ['Pump_Pressure', 'Depth_Sensor']:
        folder_path = os.path.join(directory_path, folder)
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    error_msg = f'Failed to delete {file_path}. Reason: {e}'
                    print(error_msg)
                    logger.error(error_msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port1', required=True, help='The port for the distance sensor connection')
    parser.add_argument('--port2', required=True, help='The port for the pressure sensor connection') # 0x48
    parser.add_argument('--directory', required=True, help='The directory to save the sensor data')
    args = parser.parse_args()

    try:
        adc = Adafruit_ADS1x15.ADS1115(address=int(args.port2, 16))
        GAIN = 1

        GPIO.setmode(GPIO.BCM)
        GPIO_TRIGGER = 18
        GPIO_ECHO = 24
        GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(GPIO_ECHO, GPIO.IN)

        directory_path = args.directory
        # info_msg = f'Sensor Suite -- Clearing Directory'
        # print(info_msg)
        # logger.info(info_msg)
        # clear_directory(directory_path)
        delay_time = .1
        info_msg = 'Sensor Suite -- Initialization Complete'
        print(info_msg)
        logger.info(info_msg)
        while True:
            distance = dist()
            adc_reading = adc.read_adc(3, gain=GAIN)
            if adc_reading is not None:
                pressure = .004686267155 * adc_reading - 19.09735
                print_and_save_sensor_data(distance, pressure, directory_path)
            else:
                error_msg = "Error: ADC reading is invalid"
                # print(error_msg)
                logger.error(error_msg)
            time.sleep(delay_time)
    except KeyboardInterrupt:
        info_msg = f'CTRL + C -- Measured data saved to {directory_path}'
        print(info_msg)
        logger.info(info_msg)
        GPIO.cleanup()
    except Exception as e:
        # error_msg = f"Unexpected error: {e}"
        print(error_msg)
        logger.error(error_msg)
        GPIO.cleanup()
