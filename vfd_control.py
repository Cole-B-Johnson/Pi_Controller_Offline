from utils import *
import time
import argparse
import serial

def run(vfd_folder, delay_sec, ser, slave_list, slave_name_mapping):
    print('VFD Control -- Clearing Directories')
    for slave_name in slave_name_mapping.values():
        check_directory(f'{vfd_folder}{slave_name}/To_VFD')
        check_directory(f'{vfd_folder}{slave_name}/From_VFD')

    drive_mode = speed = slave_id = None
    processed_timestamps = {}
    for slave_id, slave_name in slave_name_mapping.items():
        dir_path = f'{vfd_folder}{slave_name}/To_VFD'
        processed_timestamps[slave_id] = get_timestamps_from_files(dir_path)
    last_directory_write_time = 0

    print('VFD Control -- Initialization Complete')
    try:
        while True:
            current_time = time.time()
            for slave_ind, slave_name in slave_name_mapping.items():
                data, timestamp = check_local_folder(f'{vfd_folder}{slave_name}/To_VFD/', processed_timestamps[slave_ind])
                if data and timestamp:
                    break
            
            if data:
                drive_mode_new, speed_new, slave_id_new = process_drive_mode(data), process_speed(data), slave_ind
                # print(f'Drive Mode: {drive_mode_new}, Speed: {speed_new}, Slave ID: {slave_id_new}')
                if ((drive_mode_new != drive_mode) or (slave_id_new != slave_id)) and (drive_mode_new in [2, 4, 1]):
                    drive_mode, slave_id = drive_mode_new, slave_id_new
                    send_to_vfd(slave_id, ser, drive_mode=drive_mode)
                    processed_timestamps[slave_id].append(timestamp)
                    # print('Successfully wrote new drive mode')
                if ((speed_new != speed) or (slave_id_new != slave_id)) and (speed_new != 'OL') and (speed_new != 'NaN'):
                    speed, slave_id = speed_new, slave_id_new
                    send_to_vfd(slave_id, ser, speed=speed)
                    processed_timestamps[slave_id].append(timestamp)
                    # print('Successfully wrote new speed')

            if current_time - last_directory_write_time > delay_sec:
                vfd_output = {}
                for slave in slave_list:
                    if slave not in [1, 5]:
                        continue
                    vfd_output[slave] = read_from_vfd(slave, ser)
                    if vfd_output[slave] is None:
                        continue
                    from_vfd_folder = f'{vfd_folder}{slave_name_mapping[slave]}/From_VFD'
                    filename_from_vfd = f'output_{int(current_time)}'
                    save_to_file(filename_from_vfd, vfd_output[slave], from_vfd_folder)
                    last_directory_write_time = current_time
    except KeyboardInterrupt:
        print(f'CTRL + C -- VFD data saved to {vfd_folder}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help='The USB port for the Modbus connection')
    args = parser.parse_args()

    local_folder = '/home/levitree/Desktop' # this should be your local folder
    vfd_folder = f'{local_folder}/Live-Data-Pathways/'
    delay_sec = 10 
    slave_list = [1,3,4,5]
    slave_name_mapping = {3: 'Hydrapulper', 1: '3_Progressive_Cavity_Pump', 
                          5: '4_Progressive_Cavity_Pump', 4: 'Auger_Truck'}

    ser = serial.Serial(
        port=args.port,
        baudrate = 9600,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

    run(vfd_folder, delay_sec, ser, slave_list, slave_name_mapping)
