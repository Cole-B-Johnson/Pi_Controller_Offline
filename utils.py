import json
import struct
import pymodbus.utilities
import os
import glob
import time
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
    try:
        byte_count, data = line[2], line[3:-2]
    except:
        return None
    try:
        outputs = struct.unpack('>' + 'H' * (byte_count // 2), data)
    except:
        return None
    return json.dumps({"output_frequency": outputs[0], "input_power": outputs[1], 
            "output_current": outputs[2], "output_voltage": outputs[3], "current_mode": outputs[4]})

def clear_local_folder(directory_path: str):
    files = glob.glob(f'{directory_path}/*')
    for f in files:
        os.remove(f)


def check_local_folder(directory_path: str, processed_timestamps: list) -> Tuple[Optional[Dict], Optional[int]]:
    try:
        files = [f for f in glob.glob(f"{directory_path}/*.json")
                 if int(os.path.basename(f).split('_')[-1][:-5]) not in processed_timestamps]
    except ValueError as e:
        print(e)
        return None, None

    if files:
        latest_file = max(files, key=lambda x: int(os.path.basename(x).split('_')[-1][:-5]))
        max_retries = 5  # Number of times to retry reading the file
        wait_time = .2  # Time in seconds to wait between retries
        total_wait_time = 0  # Total time waited, to prevent infinite loops

        while max_retries > 0 and total_wait_time < 5:  # 5 seconds timeout
            try:
                with open(latest_file, 'r') as file_content:
                    data = json.load(file_content)
                return data, int(os.path.basename(latest_file).split('_')[-1][:-5])
            except json.JSONDecodeError:  # Handle JSON decode errors
                print(f"Error reading {latest_file}. Retrying...")
                max_retries -= 1
                total_wait_time += wait_time
                time.sleep(wait_time)
        
        # After max_retries or 5 seconds timeout, skip this file
        print(f"Skipping file {latest_file} after multiple failed attempts.")
        processed_timestamps.append(int(os.path.basename(latest_file).split('_')[-1][:-5]))  # Mark as read

    return None, None

def save_to_local_folder(directory_path: str, file_name: str, data: Union[Dict, str]):
    full_file_path = os.path.join(directory_path, f"{file_name}.json")
    try:
        with open(full_file_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error writing to file {file_name} in folder {directory_path}: {e}")

def check_directory(dir_path: str):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def save_to_file(file_name: str, data: Union[Dict, str], dir_path: str):
    check_directory(dir_path)
    file_path = os.path.join(dir_path, file_name + '.json')
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def get_timestamps_from_files(directory):
    files = os.listdir(directory)
    timestamps = [int(file.split('_')[1].split('.')[0]) for file in files if file.startswith('command_')]
    return timestamps
