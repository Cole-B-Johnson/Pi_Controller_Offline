from utils import *
import time
import argparse
import serial
import logging
import datetime

# Setup Logger
log_directory = "/home/levitree/Desktop/logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Generates a string with the current date and time.
log_file_name = f"vfd_control_{current_time}.log"  # Appends the timestamp to the logfile's name.
log_file_path = os.path.join(log_directory, log_file_name)

logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def run(vfd_folder, delay_sec, ser, slave_list, slave_name_mapping):
    msg = 'VFD Control -- Checking Directories'
    print(msg)
    logger.info(msg)
    
    try:
        for slave_name in slave_name_mapping.values():
            check_directory(f'{vfd_folder}{slave_name}/To_VFD')
            check_directory(f'{vfd_folder}{slave_name}/From_VFD')
    except Exception as e:
        msg = f"Error while checking or creating directories: {e}"
        print(msg)
        logger.error(msg)

    drive_mode = speed = slave_id = None
    processed_timestamps = {}

    try:
        for slave_id, slave_name in slave_name_mapping.items():
            dir_path = f'{vfd_folder}{slave_name}/To_VFD'
            processed_timestamps[slave_id] = get_timestamps_from_files(dir_path)
    except Exception as e:
        msg = f"Error while getting timestamps from files: {e}"
        print(msg)
        logger.error(msg)

    last_directory_write_time = 0

    msg = 'VFD Control -- Initialization Complete'
    print(msg)
    logger.info(msg)

    try:
        while True:
            current_time = time.time()

            # writing to vfd if new commands are written to file system
            for slave_ind, slave_name in slave_name_mapping.items():
                try:
                    data, timestamp = check_local_folder(f'{vfd_folder}{slave_name}/To_VFD/', processed_timestamps[slave_ind])
                except Exception as e:
                    msg = f"Error while checking local folder for {slave_name}: {e}"
                    print(msg)
                    logger.error(msg)
                    continue
                
                if data and timestamp:
                    drive_mode_new, speed_new, slave_id_new = process_drive_mode(data), process_speed(data), slave_ind
                    msg = f'Drive Mode: {drive_mode_new}, Speed: {speed_new}, Slave ID: {slave_id_new}'
                    print(msg)
                    logger.debug(msg)
                    
                    if ((drive_mode_new != drive_mode) or (slave_id_new != slave_id)) and (drive_mode_new in [2, 4, 1]):
                        drive_mode, slave_id = drive_mode_new, slave_id_new
                        send_to_vfd(slave_id, ser, drive_mode=drive_mode)
                        processed_timestamps[slave_id].append(timestamp)
                        msg = 'Successfully wrote new drive mode'
                        print(msg)
                        logger.info(msg)

                    if ((speed_new != speed) or (slave_id_new != slave_id)) and (speed_new != 'OL') and (speed_new != 'NaN'):
                        speed, slave_id = speed_new, slave_id_new
                        send_to_vfd(slave_id, ser, speed=speed)
                        processed_timestamps[slave_id].append(timestamp)
                        msg = 'Successfully wrote new speed'
                        print(msg)
                        logger.info(msg)
            
            # reading from vfd if reading delay has elapsed
            if current_time - last_directory_write_time > delay_sec:
                vfd_output = {}
                for slave in slave_list:
                    if slave not in [1, 3, 4, 5]:
                        continue
                    
                    msg = 'reading'
                    logger.debug(msg)
                    
                    try:
                        vfd_output[slave] = read_from_vfd(slave, ser)
                    except Exception as e:
                        msg = f"Error reading from VFD for slave {slave}: {e}"
                        print(msg)
                        logger.error(msg)
                        continue

                    if vfd_output[slave] is None:
                        continue

                    from_vfd_folder = f'{vfd_folder}{slave_name_mapping[slave]}/From_VFD'
                    filename_from_vfd = f'output_{int(current_time)}'

                    try:
                        save_to_file(filename_from_vfd, vfd_output[slave], from_vfd_folder)
                        last_directory_write_time = current_time
                    except Exception as e:
                        msg = f"Error saving file for slave {slave}: {e}"
                        print(msg)
                        logger.error(msg)
    except KeyboardInterrupt:
        msg = f'CTRL + C -- VFD data saved to {vfd_folder}'
        print(msg)
        logger.info(msg)
    except Exception as e:
        msg = f"Unexpected error in main loop: {e}"
        print(msg)
        logger.critical(msg)
    finally:
        msg = f'Data potentially saved to {vfd_folder}. Ensure data integrity and check for errors.'
        print(msg)
        logger.warning(msg)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help='The USB port for the Modbus connection')
    args = parser.parse_args()

    local_folder = '/home/levitree/Desktop' # this should be your local folder
    vfd_folder = f'{local_folder}/Live-Data-Pathways/'
    delay_sec = .25
    slave_list = [1,3,4,5]
    slave_name_mapping = {3: 'Hydrapulper', 1: '3_Progressive_Cavity_Pump', # ..., 8 inch moymo
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
