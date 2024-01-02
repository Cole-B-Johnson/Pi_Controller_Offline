from utils import *
import time
import argparse
import serial
import logging
import datetime
from auto_pilot import *

# Setup Logger
log_directory = "/home/levitree/Desktop/logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Generates a string with the current date and time.
log_file_name = f"autopilot_{current_time}.log"  # Appends the timestamp to the logfile's name.
log_file_path = os.path.join(log_directory, log_file_name)

logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def run(vfd_folder, delay_sec, slave_names, pump_to_scaling_factor, auger_truck_multiplier):
    # vfd_folder: to the live_data_pathways directory
    # delay_sec: between autopilot iterations (pressure check and command writes)
    # slave_names: vfd folder names that we write commands to
    
    # making sure the autopilot and vfd directories exist
    msg = 'Auto Pilot -- Checking Directories'
    print(msg)
    logger.info(msg)
    try:
        for slave_name in slave_names:
            check_directory(f'{vfd_folder}{slave_name}/To_VFD')
        check_directory(f'{vfd_folder}autopilot/To_VFD')
    except Exception as e:
        msg = f"Error while checking or creating directories: {e}"
        print(msg)
        logger.error(msg)

    # looking at already present files in autopilot folder and pressure folder and distance folder
    try:
        # look at the folders we read from
        # autopilot
        dir_path = f'{vfd_folder}autopilot/To_VFD'
        processed_timestamps_autopilot = get_timestamps_from_files(dir_path)
        # pressure
        dir_path = f'{vfd_folder}Pump_Pressure'
        processed_timestamps_pressure = get_timestamps_from_files(dir_path)
        # mix tank distance sensor
        dir_path = f'{vfd_folder}Depth_Sensor'
        processed_timestamps_distance = get_timestamps_from_files(dir_path)

    except Exception as e:
        msg = f"Error while getting timestamps from files: {e}"
        print(msg)
        logger.error(msg)

    last_directory_write_time = 0

    msg = 'Auto Pilot -- Initialization Complete'
    print(msg)
    logger.info(msg)

    # main loop:
    autopilot_enabled = False
    depth_goal = 0
    current_pressure = 0
    current_distance = 0
    last_check_time = 0

    # little bug in here somewhere that made me remove the check if the modes are not equal: wouldnt add the processed time stamps for autopilot and would infinitely check same file
    try:
        while True:
            current_time = time.time()
            if current_time - last_check_time > delay_sec:
                last_check_time = time.time()
                # check if auto pilot should be on...
                # check autopilot folder for new files
                try:
                    autopilot_data, autopilot_timestamp = check_local_folder(f'{vfd_folder}autopilot/To_VFD/', processed_timestamps_autopilot)
                except Exception as e:
                    msg = f"Error while checking local folder for autopilot commands: {e}"
                    print(msg)
                    logger.error(msg)
                    continue
                # if there are new files, check for validity and update either mode or depth goal
                if autopilot_data and autopilot_timestamp:
                    autopilot_mode_new, depth_new = process_autopilot_mode(autopilot_data), process_inputted_depth(autopilot_data)
                    msg = f'Auto Pilot Mode: {autopilot_mode_new}, Inputted Depth: {depth_new}'
                    print(msg)
                    logger.debug(msg)
                    
                    # Mode
                    if (autopilot_mode_new in [True, False]):
                        autopilot_enabled = autopilot_mode_new
                        processed_timestamps_autopilot.append(autopilot_timestamp)
                        msg = f'Auto Pilot mode switched to {autopilot_enabled}'
                        print(msg)
                        logger.info(msg)
                    
                    # Depth
                    if (depth_new != depth_goal) and (depth_new != 'OL') and (depth_new != 'NaN'):
                        depth_goal = depth_new
                        processed_timestamps_autopilot.append(autopilot_timestamp)
                        msg = f'Goal Depth switched to {depth_goal}'
                        print(msg)
                        logger.info(msg)

                
                # Update current pressure measurements if available
                try:
                    pressure_data, pressure_timestamp = check_local_folder(f'{vfd_folder}Pump_Pressure/', processed_timestamps_pressure)
                except Exception as e:
                    msg = f"Error while checking local folder for pressure readings: {e}"
                    print(msg)
                    logger.error(msg)
                    continue

                # if there are new files, check for validity and update current pressure
                if pressure_data and pressure_timestamp:
                    pressure_new = process_pressure(pressure_data)
                    current_pressure = pressure_new
                    processed_timestamps_pressure.append(pressure_timestamp)
                    msg = f'Pressure: {pressure_new}'
                    # print(msg)
                    logger.debug(msg)
                
                # Update current distance measurements if available
                try:
                    distance_data, distance_timestamp = check_local_folder(f'{vfd_folder}Depth_Sensor/', processed_timestamps_distance)
                except Exception as e:
                    msg = f"Error while checking local folder for depth readings: {e}"
                    print(msg)
                    logger.error(msg)
                    continue

                # if there are new files, check for validity and update current distance
                if distance_data and distance_timestamp:
                    distance_new = process_depth(distance_data)
                    current_distance = distance_new
                    processed_timestamps_distance.append(pressure_timestamp)
                    msg = f'Distance: {distance_new}'
                    # print(msg)
                    logger.debug(msg)
                            
                if autopilot_enabled:
                    if (current_distance > 50) or (current_distance < 30):
                        for vfd_name in slave_names:
                            write_command_for_vfds_to_file(vfd_folder, mode='stop', vfd=vfd_name)
                    
                    # get difference between current and desired depths
                    # find volumetric proportions between pumps based on current psi and respective hz (how to get proportion?)
                    
                    # (still need the hz to volume of auger truck pump)
                    #    scale proportion and recompute hz to increase level 10% more than it is being emptied and vice versa for lowering level
                    #       inlets - outlet (8 inch moymo) / inlets = .1
                    
                    # scale the current rate of volumes to find desired rate of volumes for each of the pumps and auger truck with respect to outlet
                    # outlet_volume_rate = get_volume(current_pressure, latest_vfd_outputs['3_Progressive_Cavity_Pump']['hz'], pump_to_scaling_factor['3_Progressive_Cavity_Pump'])

                    # # need to scale proportionally based on this outlet volume rate by either 1.25 or .75

                    # # find the Hz required for the pumps and auger truck based on these computed new desired rate of volumes
                    # for current_pump in [x for x in slave_names if x != 'Auger_Truck' and x != '3_Progressive_Cavity_Pump']:
                    #     find_required_hz_pumps(current_pressure, pump_to_scaling_factor[current_pump], desired_volume[current_pump])
                    # find_required_hz_auger_truck(auger_truck_multiplier, desired_volume['Auger_Truck'])

                
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

    local_folder = '/home/levitree/Desktop' # this should be your local folder
    vfd_folder = f'{local_folder}/Live-Data-Pathways/'
    delay_sec = .25
    slave_names = ['Hydrapulper', '3_Progressive_Cavity_Pump', # ..., 8 inch moymo
                        '4_Progressive_Cavity_Pump', 'Auger_Truck']
    
    pump_to_scaling_factor = {'Hydrapulper': 3.44, '3_Progressive_Cavity_Pump': .1168, # ..., 8 inch moymo
                        '4_Progressive_Cavity_Pump': 3.44}
    
    auger_truck_multiplier = 1 # hz to rate of volumetric deposition

    run(vfd_folder, delay_sec, slave_names, pump_to_scaling_factor, auger_truck_multiplier)
