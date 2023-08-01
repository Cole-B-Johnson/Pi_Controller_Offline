import time
import argparse
import boto3
import json
import RPi.GPIO as GPIO
import Adafruit_ADS1x15

def save_to_bucket(bucket_name, data):
    s3 = boto3.client('s3', aws_access_key_id='AKIAVP5ZAHNW7TWQDNEG', aws_secret_access_key = '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')
    file_name = f'sensor_data_{int(time.time())}'
    key_pressure = f'Live-Data-Pathways/Pump_Pressure/{file_name}'
    key_distance = f'Live-Data-Pathways/Depth_Sensor/{file_name}'
    encoded_data_distance = json.dumps(data['distance_sensor']).encode('utf-8')
    encoded_data_pressure = json.dumps(data['pressure_sensor']).encode('utf-8')
    try:
        s3.put_object(Body=encoded_data_distance, Bucket=bucket_name, Key=key_distance)
    except Exception as e:
        print(f"Error writing to file {key_distance} in bucket {bucket_name}: {e}")
    try:
        s3.put_object(Body=encoded_data_pressure, Bucket=bucket_name, Key=key_pressure)
    except Exception as e:
        print(f"Error writing to file {key_pressure} in bucket {bucket_name}: {e}")

def print_and_save_sensor_data(dis, pressure, bucket_name):
    print(f"Mix Tank Distance {dis} mm")
    print(f"Pressure Sensor Reading: {pressure}")
    
    data = {'distance_sensor': dis, 'pressure_sensor': pressure}
    save_to_bucket(bucket_name, data)

def clear_bucket_folder(bucket_name):
    s3 = boto3.client('s3', aws_access_key_id='AKIAVP5ZAHNW7TWQDNEG', aws_secret_access_key = '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')

    prefixes = ['Live-Data-Pathways/Pump_Pressure', 'Live-Data-Pathways/Depth_Sensor']

    for prefix in prefixes:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        for page in pages:
            if 'Contents' in page:
                delete = {'Objects': [{'Key':obj['Key']} for obj in page['Contents']]}
                s3.delete_objects(Bucket=bucket_name, Delete=delete)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port1', required=True, help='The port for the distance sensor connection')
    parser.add_argument('--port2', required=True, help='The port for the pressure sensor connection') # 0x48
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
    
    # S3
    bucket_name = 'levitree-main'
    print(f'Sensor Suite -- Clearing Buckets')
    clear_bucket_folder(bucket_name)
    delay_time = .1
    print('Sensor Suite -- Initialization Complete')
    try:
        while True:
            distance = dist()
            adc_reading = adc.read_adc(3, gain=GAIN)
            pressure = .004686267155 * adc_reading - 19.09735 # relation for 5v and 150psi sensor
            print_and_save_sensor_data(distance, pressure, bucket_name)
            time.sleep(delay_time)
    except KeyboardInterrupt:
        print(f'CTRL + C -- Measured data saved to {bucket_name}')
        GPIO.cleanup()
