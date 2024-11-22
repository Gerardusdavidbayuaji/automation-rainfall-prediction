# ===================================================================================== TESTING V1 ====================================================================
# import netCDF4 as nc
# import pandas as pd
# import numpy as np

# # Buka file NetCDF
# file_path = "repository/input/ECMWF.0125.202410311200.PREC.nc"  # Ganti dengan path file Anda
# dataset = nc.Dataset(file_path)

# # Ambil data dari dataset
# latitudes = dataset.variables['lat'][:]
# longitudes = dataset.variables['lon'][:]
# times = dataset.variables['time'][:]
# rainfall = dataset.variables['tp'][:]

# # Konversi waktu jika diperlukan
# # (Asumsikan waktu dalam detik sejak epoch, ubah sesuai dengan format file NetCDF Anda)
# time_units = dataset.variables['time'].units
# time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'
# time_converted = nc.num2date(times, units=time_units, calendar=time_calendar)

# # Buat struktur DataFrame
# data = []
# for time_index, time_value in enumerate(time_converted):
#     for lat_index, lat in enumerate(latitudes):
#         for lon_index, lon in enumerate(longitudes):
#             rain_value = rainfall[time_index, 0, lat_index, lon_index]
#             data.append([lat, lon, time_value, rain_value])

# # Buat DataFrame
# df = pd.DataFrame(data, columns=['Latitude', 'Longitude', 'Time', 'Rainfall'])

# # Tampilkan 100 data awal dan 100 data akhir
# first_100_data = df.head(100)
# last_100_data = df.tail(100)

# # Gabungkan kedua data tersebut
# combined_df = pd.concat([first_100_data, last_100_data])

# # Simpan ke file Excel
# output_file = "repository/output/PREC_202410311200_first_last_100.xlsx"
# combined_df.to_excel(output_file, index=False)
# print(f"Data telah disimpan dalam {output_file}")

# ===================================================================================== TESTING V2 ==================================================================== 
# import netCDF4 as nc
# import pandas as pd
# import numpy as np
# import cftime
# from datetime import datetime

# file_path = "repository/input/ECMWF.0125.202410311200.PREC.nc" 
# dataset = nc.Dataset(file_path)

# latitudes = dataset.variables['lat'][:]
# longitudes = dataset.variables['lon'][:]
# times = dataset.variables['time'][:]
# rainfall = dataset.variables['tp'][:]

# time_units = dataset.variables['time'].units
# time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'
# time_converted = nc.num2date(times, units=time_units, calendar=time_calendar)

# time_converted_3hr = []
# for time_value in time_converted:
#     if isinstance(time_value, cftime._cftime.DatetimeGregorian):
#         time_value = datetime(time_value.year, time_value.month, time_value.day, 
#                               time_value.hour, time_value.minute, time_value.second)
#     rounded_time = pd.to_datetime(time_value).round('3H')  
#     time_converted_3hr.append(rounded_time)

# data = []
# for time_index, time_value in enumerate(time_converted_3hr):
#     for lat_index, lat in enumerate(latitudes):
#         for lon_index, lon in enumerate(longitudes):
#             rain_value = rainfall[time_index, 0, lat_index, lon_index]
#             data.append([round(lat, 15), round(lon, 15), time_value, rain_value])

# df = pd.DataFrame(data, columns=['Latitude', 'Longitude', 'Time', 'Rainfall'])

# output_file = "repository/output/PREC_202410311200_3hr.csv"
# df.to_csv(output_file, index=False)
# print(f"Data telah disimpan dalam {output_file}")

# ===================================================================================== TESTING V3 ====================================================================
# import netCDF4 as nc
# import pandas as pd
# import numpy as np
# import cftime
# from datetime import datetime

# # Buka file NetCDF
# file_path = "repository/input/ECMWF.0125.202410311200.PREC.nc" 
# dataset = nc.Dataset(file_path)

# # Ambil data dari dataset
# latitudes = dataset.variables['lat'][:]
# longitudes = dataset.variables['lon'][:]
# times = dataset.variables['time'][:]
# rainfall = dataset.variables['tp'][:]

# # Konversi waktu jika diperlukan
# time_units = dataset.variables['time'].units
# time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'
# time_converted = nc.num2date(times, units=time_units, calendar=time_calendar)

# # Ubah waktu menjadi data per 3 jam
# time_converted_3hr = []
# for time_value in time_converted:
#     if isinstance(time_value, cftime._cftime.DatetimeGregorian):
#         time_value = datetime(time_value.year, time_value.month, time_value.day, 
#                               time_value.hour, time_value.minute, time_value.second)
#     rounded_time = pd.to_datetime(time_value).round('3H')  
#     time_converted_3hr.append(rounded_time)

# # Buat struktur DataFrame
# data = []
# for time_index, time_value in enumerate(time_converted_3hr):
#     for lat_index, lat in enumerate(latitudes):
#         for lon_index, lon in enumerate(longitudes):
#             rain_value = rainfall[time_index, 0, lat_index, lon_index]
#             data.append([round(lat, 15), round(lon, 15), time_value, rain_value])

# # Konversi data ke dalam DataFrame
# df = pd.DataFrame(data, columns=['y', 'x', 'time', 'z'])

# # Pisahkan berdasarkan bulan, hari, tahun, dan jam
# df['Year'] = df['time'].dt.year
# df['Month'] = df['time'].dt.month
# df['Day'] = df['time'].dt.day
# df['Hour'] = df['time'].dt.hour

# # Loop melalui setiap waktu unik untuk menyimpan data ke CSV
# unique_times = df['time'].unique()
# output_dir = "repository/output/"

# for unique_time in unique_times:
#     # Filter data berdasarkan waktu
#     filtered_df = df[df['time'] == unique_time]
    
#     # Buat nama file berdasarkan bulan, hari, tahun, dan jam
#     time_str = unique_time.strftime('%m%d%Y_%H%M%S')
#     output_file = f"{output_dir}PREC_{time_str}.csv"
    
#     # Simpan data ke CSV
#     filtered_df[['y', 'x', 'time', 'z']].to_csv(output_file, index=False)
#     print(f"Data untuk {unique_time} disimpan di {output_file}")

# ===================================================================================== TESTING V4 ====================================================================
import os
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import griddata
import rasterio
from rasterio.transform import from_origin

# Fungsi IDW
def idw_interpolation(x, y, z, xi, yi, power=2):
    tree = cKDTree(np.array(list(zip(x, y))))
    dist, idx = tree.query(np.array(list(zip(xi.ravel(), yi.ravel()))), k=10)
    weights = 1 / dist**power
    weights /= weights.sum(axis=1, keepdims=True)
    zi = np.sum(z[idx] * weights, axis=1)
    return zi.reshape(xi.shape)

# Folder input dan output
input_dir = "repository/output/"
output_dir = "repository/output/idw/"
os.makedirs(output_dir, exist_ok=True)

# Baca file CSV di folder output
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

# Grid untuk interpolasi
grid_x, grid_y = np.meshgrid(
    np.linspace(-180, 180, 360),  # Longitudes
    np.linspace(-90, 90, 180)    # Latitudes
)

# Proses tiap file CSV
for csv_file in csv_files:
    csv_path = os.path.join(input_dir, csv_file)
    df = pd.read_csv(csv_path)

    # Ambil koordinat (x, y) dan nilai (z)
    x = df['x'].values
    y = df['y'].values
    z = df['z'].values

    # Interpolasi IDW
    grid_z = idw_interpolation(x, y, z, grid_x, grid_y)

    # Simpan hasil ke GeoTIFF
    output_file = os.path.join(output_dir, f"{os.path.splitext(csv_file)[0]}.tiff")
    transform = from_origin(-180, 90, 1.0, 1.0)  # Resolusi grid 1 derajat
    with rasterio.open(
        output_file,
        'w',
        driver='GTiff',
        height=grid_z.shape[0],
        width=grid_z.shape[1],
        count=1,
        dtype=grid_z.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(grid_z, 1)

    print(f"Hasil interpolasi disimpan di {output_file}")