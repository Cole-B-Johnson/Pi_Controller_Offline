import boto3
import json
import struct
import pymodbus.utilities
from typing import Tuple, Optional, Dict, Union

def create_modbus_rtu_command(device_id: int, function_code: int, 
                              starting_address: int, num_registers: int) -> bytes:
    command_without_crc = struct.pack('!B B H H', device_id, function_code, 
                                      starting_address, num_registers)
    crc = pymodbus.utilities.computeCRC(command_without_crc)
    crc_bytes = struct.pack('>H', crc)
    command_with_crc = command_without_crc + crc_bytes
    return command_with_crc

def get_value(file_data: Dict, key: str, default: Union[str, int]) -> Union[str, int]:
    if not isinstance(file_data, dict):
        print("File data should be a dictionary.")
        return default
    return file_data.get(key, default)

def get_user_drive(file_data: Dict) -> Union[int, str]:
    drive_mode_map = {"fwd": 1, "rev": 2, "stop": 4}
    drive_input = get_value(file_data, 'drive_mode', "")
    return drive_mode_map.get(drive_input, "Drive Error")

def get_user_speed(file_data: Dict) -> Union[int, str]:
    speed_input = get_value(file_data, 'speed', "NaN")
    try:
        speed_int = int(float(speed_input)*100)
        return speed_int if 0 <= speed_int <= 9500 else "OL"
    except ValueError:
        return "NaN"

def get_slave_id(file_data: Dict) -> Union[int, str]:
    return get_value(file_data, 'slave_id', "NaN")

def process_drive_mode(data):
    drive_mode = get_user_drive(data)
    return drive_mode

def process_speed(data):
    speed = get_user_speed(data)
    return speed

def process_slave_id(data):
    slave_id = get_slave_id(data)
    if slave_id == "NaN":
        print("Slave ID entered is not a number")
    else:
        print(f"Slave ID set to {slave_id}")
        return slave_id
    return slave_id

def send_to_vfd(device_id: int, ser, drive_mode: Optional[int]=None, speed: Optional[int]=None):
    function_code = 6
    if drive_mode is None and speed is None:
        print('Improper input to send_to_VFD, skipping command')
        return
    starting_address = 0x706 if drive_mode else 0x705
    num_registers = drive_mode if drive_mode else speed
    command = create_modbus_rtu_command(device_id, function_code, 
                                        starting_address, num_registers)
    while True:
        ser.write(command)
        line = ser.readline()
        if line != b'' and not all(byte == 0xff for byte in line):
            break

def read_from_vfd(device_id: int, ser) -> Dict[str, int]:
    mapping = {1: b'\x01\x03\x08\x09\x00\x06\x17\xAA', # 1 
               3: b'\x03\x03\x08\x09\x00\x06\x16\x48', # 3
               4: b'\x04\x03\x08\x09\x00\x06\x17\xFF', # 4
               5: b'\x05\x03\x08\x09\x00\x06\x16\x2E'} # 5
    
    try:
        ser.write(mapping[device_id])
    except KeyError:
        raise Exception(f"Device ID {device_id} not found in mapping.")

    line = ser.readline()
    print(line)
    try:
        byte_count, data = line[2], line[3:-2]
    except:
        return None
    print(data)
    try:
        outputs = struct.unpack('>' + 'H' * (byte_count // 2), data)
    except:
        return None
    print(outputs)
    return json.dumps({"output_frequency": outputs[0], "input_power": outputs[1], 
            "output_current": outputs[2], "output_voltage": outputs[3], "current_mode": outputs[4]})

def clear_bucket(bucket_name: str, folder_name: str):
    s3 = boto3.client('s3', aws_access_key_id='AKIAVP5ZAHNW7TWQDNEG', aws_secret_access_key = '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')

    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=folder_name)

    for page in pages:
        if 'Contents' in page:
            delete = {'Objects': [{'Key':obj['Key']} for obj in page['Contents']]}
            s3.delete_objects(Bucket=bucket_name, Delete=delete)

def check_bucket(bucket: str, folder: str, processed_timestamps: list) -> Tuple[Optional[Dict], Optional[int]]:
    s3 = boto3.resource('s3', aws_access_key_id='AKIAVP5ZAHNW7TWQDNEG', aws_secret_access_key = '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')
    bucket_object = s3.Bucket(bucket)
    contents = [object.key for object in bucket_object.objects.filter(Prefix=folder)][1:]
    try:
        files = [obj for obj in contents if int(obj.split('_')[-1][:-5]) not in processed_timestamps]
    except ValueError as e:
        print(e)
        return None, None
    if files:
        latest_file = max(files, key=lambda x: int(x.split('_')[-1][:-5]))
        s3_object = s3.Object(bucket, latest_file)
        file_content = s3_object.get()['Body'].read().decode('utf-8')
        return json.loads(file_content), int(latest_file.split('_')[-1][:-5])
    return None, None

def save_to_bucket(bucket_name: str, folder_name: str, 
                   file_name: str, data: Union[Dict, str]):
    s3 = boto3.client('s3', aws_access_key_id='AKIAVP5ZAHNW7TWQDNEG', aws_secret_access_key = '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')
    key = folder_name + '/' + file_name + '.json'
    encoded_data = str(data).encode('utf-8')
    try:
        s3.put_object(Body=encoded_data, Bucket=bucket_name, Key=key)
    except Exception as e:
        print(f"Error writing to file {file_name} in bucket {bucket_name}: {e}")
