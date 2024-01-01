def create_volume_interpolator(data):
    """
    Creates a volume interpolator function based on the provided data.

    Args:
    data (dict): A dictionary containing PSI and volume data for different RPMs.

    Returns:
    function: A function that takes PSI, Hz, and a scaling factor as arguments and returns the interpolated volume.
    """
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator, griddata

    # Generate data points along each best fit line for every psi value
    generated_data = {}
    for i in data:
        x, y = data[i][:, 0], data[i][:, 1]
        coefficients = np.polyfit(x, y, 2)
        polynomial = np.poly1d(coefficients)
        x_range = np.arange(int(min(x)), int(max(x)) + 1)
        y_range = polynomial(x_range)
        generated_data[i] = (x_range, y_range)

    # Prepare combined data for interpolation
    combined_data = np.array([[x, rpm, y] for rpm, (x_vals, y_vals) in zip([100, 200, 300, 350], generated_data.values()) for x, y in zip(x_vals, y_vals)])

    # Extracting x, y, and volume data for interpolation
    x_data, y_data, volume_data = combined_data[:, 0], combined_data[:, 1], combined_data[:, 2]

    # Setting up grid for interpolation
    psi_range = np.linspace(min(x_data), max(x_data), 100)
    rpm_range = np.linspace(min(y_data), max(y_data), 100)

    # Creating an interpolating function
    psi_grid, rpm_grid = np.meshgrid(psi_range, rpm_range)
    volume_interpolated = griddata((x_data, y_data), volume_data, (psi_grid, rpm_grid), method='linear')
    interpolator = RegularGridInterpolator((psi_range, rpm_range), volume_interpolated.T)  # Transpose needed

    # Define the function to get volume
    def get_volume(psi, hz, scaling_factor):
        rpm = hz * scaling_factor
        if psi < min(psi_range) or psi > max(psi_range) or rpm < min(rpm_range) or rpm > max(rpm_range):
            return "Pressure or Hz out of bounds"
        return interpolator([[psi, rpm]])[0]

    return get_volume

# Example data
data_example = {
    1: np.array([[0, 55], [45, 41], [75, 0]]),
    2: np.array([[0, 120], [47, 100], [86, 40]]),
    3: np.array([[0, 190], [42, 175], [87, 110]]),
    4: np.array([[0, 235], [47, 215], [84, 160]])
}

# Create the volume interpolator function
volume_interpolator = create_volume_interpolator(data_example)

# # Example usage of the created function
# example_psi = 30
# example_hz = 2.5
# scaling_factor = 60
# example_volume = volume_interpolator(example_psi, example_hz, scaling_factor)
# # example_psi, example_hz, example_volume




# # Prepare the structured data for JSON serialization
# structured_interpolator_data = {
#     'psi_range': psi_range.tolist(),  # Convert numpy array to list for JSON serialization
#     'rpm_range': rpm_range.tolist(),
#     'volume_interpolated': volume_interpolated.tolist()
# }

# # Save the structured data to a JSON file
# json_interpolator_filename = '/mnt/data/structured_interpolator_data.json'
# with open(json_interpolator_filename, 'w') as file:
#     json.dump(structured_interpolator_data, file)

# json_interpolator_filename

