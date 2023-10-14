import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math


reference_lat = 46.4  # Replace with your latitude
reference_lon = 8.9   # Replace with your longitude
reference_alt = 470   # Replace with your altitude

dotsize = 5 #Size of the dots in the diagram



earth_radius = 6371000 

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Generate a polar diagram from log files.')
parser.add_argument('--nodfm', action='store_true', help='Do not use data from DFM sondes')
parser.add_argument('logfiles', nargs='+', help='List of log files to process')
args = parser.parse_args()

# Initialize data as an empty DataFrame
data = pd.DataFrame(columns=[
    'timestamp', 'serial', 'frame', 'lat', 'lon', 'alt', 'vel_v', 'vel_h',
    'heading', 'temp', 'humidity', 'pressure', 'type', 'freq_mhz', 'snr',
    'f_error_hz', 'sats', 'batt_v', 'burst_timer', 'aux_data'
])


for logfile in args.logfiles:
    if args.nodfm and "DFM" in logfile:
        continue
    temp_data = pd.read_csv(logfile)
    data = pd.concat([data, temp_data], ignore_index=True)
    
# Do not use sondes with unknown SNR

    data = data[data['snr'] != -99.0]

latitudes = data['lat']
longitudes = data['lon']
snr_values = data['snr']
altitudes = data['alt']


# Define a function to calculate azimuth
def calculate_azimuth(observer_lat, observer_lon, balloon_lat, balloon_lon):
    observer_lat = math.radians(observer_lat)
    observer_lon = math.radians(observer_lon)
    balloon_lat = math.radians(balloon_lat)
    balloon_lon = math.radians(balloon_lon)

    d_lon = balloon_lon - observer_lon

    y = math.sin(d_lon) * math.cos(balloon_lat)
    x = math.cos(observer_lat) * math.sin(balloon_lat) - math.sin(observer_lat) * math.cos(balloon_lat) * math.cos(d_lon)

    azimuth = math.atan2(y, x)
    azimuth = math.degrees(azimuth)
    azimuth = (azimuth + 360) % 360  # Ensure the result is between 0 and 360 degrees

    return azimuth

azimuths = []  # List to store calculated azimuth values

for i in range(len(latitudes)):
    azimuth = calculate_azimuth(reference_lat, reference_lon, latitudes[i], longitudes[i])
    azimuths.append(azimuth)


# Calculate distances in meters
distances = earth_radius * np.arccos(np.sin(np.radians(reference_lat)) * np.sin(np.radians(latitudes)) + np.cos(np.radians(reference_lat)) * np.cos(np.radians(latitudes)) * np.cos(np.radians(longitudes - reference_lon)))

# Calculate height difference due to earth curvature
hdiff=earth_radius * (1 - np.cos(np.radians(8.993e-6*distances))) # 0.00899 degree per km

# Calculate elevation based on altitude and distance from reference point
elevations = np.degrees(np.arctan((altitudes - reference_alt - hdiff) / distances))  # Invert elevations

# Calculate the line of sight distance for SNR normalization
distances_los = np.sqrt(distances**2 + altitudes**2)


# Normalizing SNR to 100 km distance
snr_values = data['snr'].astype(float)
snr_values = snr_values - 20 * np.log10(100000 / distances_los)

# Create a polar plot
plt.figure(figsize=(8, 8))
ax = plt.subplot(111, projection='polar', theta_direction=-1)  # Counterclockwise direction

# Map SNR values to colors (use 'snr_values' for color mapping)
colors = plt.cm.viridis(snr_values / snr_values.max())

# Plot data points on the polar diagram with color mapping
scatter = ax.scatter(np.radians(azimuths), elevations, c=snr_values, cmap='viridis', s=dotsize)

# Set colorbar for SNR values with custom ticks and labels
cbar = plt.colorbar(scatter)
cbar.set_label('SNR(100km)')

# Define custom colorbar ticks and labels based on the actual SNR range
min_snr = snr_values.min()
max_snr = snr_values.max()
cbar.set_ticks([min_snr, max_snr])
cbar.set_ticklabels([f"{min_snr:.2f}", f"{max_snr:.2f}"])


# Customize the polar plot if needed (e.g., labels, title)
plt.title('Sky chart')
plt.grid(True)

# Set the zero location to the top (North)
ax.set_theta_zero_location('N')

# Set the y-axis limits to go from 0 to 90°
#ax.set_ylim(0, 90)

# Invert the y-axis
ax.invert_yaxis()

# Show the polar diagram
#plt.gcf().set_size_inches(100, 100)
#plt.savefig('plot.png', dpi=100)  #for saving the file in higher resolution
plt.show()
