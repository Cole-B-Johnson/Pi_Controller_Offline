import json
import numpy as np
from scipy.interpolate import RegularGridInterpolator

def get_volume(psi, hz, scaling_factor):
    # 8 inch moymo scaling factor: .1168
    # 3 inch moymo scaling factor: 3.44
    # Load the JSON file
    with open('util_files/structured_interpolator_data.json', 'r') as file:
        data = json.load(file)

    # Convert the lists back to NumPy arrays
    psi_range = np.array(data['psi_range'])
    rpm_range = np.array(data['rpm_range'])
    volume_interpolated = np.array(data['volume_interpolated'])

    # Create the interpolator
    interpolator = RegularGridInterpolator((psi_range, rpm_range), volume_interpolated.T)  # Transpose if necessary

    # Convert Hz to RPM
    rpm = hz * scaling_factor

    # Find the closest values in the psi and rpm ranges
    closest_psi = min(psi_range, key=lambda x: abs(x - psi))
    closest_rpm = min(rpm_range, key=lambda x: abs(x - rpm))

    # Return the interpolated volume for the closest psi and rpm
    return interpolator([[closest_psi, closest_rpm]])[0]

# # Example usage
# example_psi = 30
# example_hz = 2.5
# scaling_factor = 60
# volume = get_volume(example_psi, example_hz, scaling_factor)
# print(f"Volume: {volume}")


def find_required_hz_pumps(psi, scaling_factor, desired_volume_rate):

    with open('util_files/structured_interpolator_data.json', 'r') as file:
        data = json.load(file)

    # Convert the lists back to NumPy arrays
    psi_range = np.array(data['psi_range'])
    rpm_range = np.array(data['rpm_range'])
    volume_interpolated = np.array(data['volume_interpolated'])
    # Create the interpolator
    interpolator = RegularGridInterpolator((psi_range, rpm_range), volume_interpolated.T)

    # Convert Hz to RPM for the entire range
    rpm_values = rpm_range / scaling_factor

    # Find the closest psi index
    psi_index = np.argmin(np.abs(psi_range - psi))

    # Extracting the volume data for the specific psi row
    volume_data_at_psi = interpolator((psi_range, rpm_values * scaling_factor))[:, psi_index]

    # Find the index of the Hz value closest to the desired volume rate
    closest_volume_index = np.argmin(np.abs(volume_data_at_psi - desired_volume_rate))

    # Find the corresponding Hz value
    closest_hz = rpm_values[closest_volume_index]

    return closest_hz

def find_required_hz_auger_truck(auger_truck_multiplier, desired_volume):
    return desired_volume / auger_truck_multiplier
