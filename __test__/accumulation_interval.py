# ======================================================== AKUMULASI ============================================================
# import os
# import netCDF4 as nc
# import pandas as pd
# import numpy as np
# from netCDF4 import num2date
# import datetime

# file_path = "repository/input/data_raster/ECMWF.0125.202410311200.PREC.nc"
# output_dir = "repository/output/daily/nc_to_csv"

# os.makedirs(output_dir, exist_ok=True)

# data = nc.Dataset(file_path)
# print(data)

# latitude = data.variables["lat"][:]
# longitude = data.variables["lon"][:]
# times = data.variables["time"][:]
# rainfall = data.variables["tp"][:] 

# dates_utc = num2date(times, data.variables["time"].units)

# df_list = []

# for i, date in enumerate(dates_utc):
#     date_str = date.strftime('%Y%m%d')
    
#     daily_rainfall = np.sum(rainfall[i], axis=0)
    
#     lat_lon_rainfall = zip(np.tile(latitude, len(longitude)), np.repeat(longitude, len(latitude)), daily_rainfall.flatten())
    
#     for lat, lon, value in lat_lon_rainfall:
#         df_list.append([lat, lon, value])
    
#     df = pd.DataFrame(df_list, columns=["latitude", "longitude", "value"])

#     output_file = os.path.join(output_dir, f"AK_PREC_{date_str}.csv")
#     df.to_csv(output_file, index=False)
    
#     df_list.clear()

# print("Processing complete.")

# ======================================================== INTERVAL ============================================================
# import os
# import netCDF4 as nc
# import pandas as pd
# import numpy as np
# from netCDF4 import num2date
# import datetime

# # Define the file path and the output directory
# file_path = "repository/input/data_raster/ECMWF.0125.202410311200.PREC.nc"
# output_dir = "repository/output/daily/nc_to_csv"

# # Make sure the output directory exists
# os.makedirs(output_dir, exist_ok=True)

# # Read the .nc data
# data = nc.Dataset(file_path)
# print(data)  # Print the dataset structure

# # Get latitude, longitude, time, and rainfall data
# latitude = data.variables["lat"][:]
# longitude = data.variables["lon"][:]
# times = data.variables["time"][:]
# rainfall = data.variables["tp"][:]  # Total precipitation

# # Convert time units to date objects
# dates_utc = num2date(times, data.variables["time"].units)

# # Create a DataFrame to store the results
# df_list = []

# # Iterate over the dates and calculate the interval precipitation
# for i in range(1, len(dates_utc)):  # Start from the second time step to calculate interval
#     date = dates_utc[i]
#     prev_date = dates_utc[i-1]

#     # Format the date as YYYYMMDD for the output filename
#     date_str = date.strftime('%Y%m%d')

#     # Calculate the rainfall interval (difference between current and previous time step)
#     interval_rainfall = rainfall[i] - rainfall[i-1]  # Interval rainfall = current - previous

#     # Ensure no negative rainfall values (set to 0 if negative)
#     interval_rainfall[interval_rainfall < 0] = 0

#     # Flatten the arrays to create a list of values for each lat-lon pair
#     lat_lon_rainfall = zip(np.tile(latitude, len(longitude)), np.repeat(longitude, len(latitude)), interval_rainfall.flatten())
    
#     # Append to the DataFrame list
#     for lat, lon, value in lat_lon_rainfall:
#         df_list.append([lat, lon, value])
    
#     # Convert the list to a DataFrame
#     df = pd.DataFrame(df_list, columns=["latitude", "longitude", "value"])

#     # Save the DataFrame to a CSV file
#     output_file = os.path.join(output_dir, f"PREC_{date_str}.csv")
#     df.to_csv(output_file, index=False)
    
#     # Clear the list for the next interval
#     df_list.clear()

# print("Processing complete.")

# ========================================================= nc to csv fix ========================================================= 
# import os
# import netCDF4 as nc
# import pandas as pd
# import numpy as np
# import cftime
# from datetime import datetime

# os.environ["PROJ_LIB"] = "C:/Users/2ndba/anaconda3/Library/share/proj"

# file_path = "repository/input/data_raster/ECMWF.0125.202410311200.PREC.nc"
# output_nc_to_csv = "repository/output/hours/nc_to_csv"
# output_csv_to_idw = "repository/output/hours/csv_to_idw"

# # Buka file NetCDF
# dataset = nc.Dataset(file_path)

# # Ambil data dari dataset
# latitudes = dataset.variables['lat'][:]
# longitudes = dataset.variables['lon'][:]
# times = dataset.variables['time'][:]
# rainfall = dataset.variables['tp'][:]

# # Konversi waktu menggunakan UTC
# time_units = dataset.variables['time'].units
# time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'

# # Konversi waktu dengan memastikan hasil adalah datetime
# time_converted = nc.num2date(times, units=time_units, calendar=time_calendar)

# # Pastikan semua elemen dikonversi menjadi datetime.datetime
# time_converted_utc = []
# for time_value in time_converted:
#     if isinstance(time_value, cftime.datetime):  # Jika tipe cftime
#         time_value = datetime(
#             time_value.year, time_value.month, time_value.day,
#             time_value.hour, time_value.minute, time_value.second
#         )
#     time_converted_utc.append(time_value)

# # Konversi ke Pandas Timestamp dan tambahkan zona waktu UTC
# time_converted_utc = pd.to_datetime(time_converted_utc).tz_localize('UTC')

# # Ubah waktu menjadi data per 3 jam
# time_converted_3hr = time_converted_utc.round('3H')

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

# for unique_time in unique_times:
#     # Filter data berdasarkan waktu, dan buat salinan eksplisit
#     filtered_df = df[df['time'] == unique_time].copy()
    
#     # Hapus informasi zona waktu dari kolom 'time'
#     filtered_df['time'] = filtered_df['time'].dt.tz_localize(None)
    
#     # Buat nama file berdasarkan bulan, hari, tahun, dan jam
#     time_str = unique_time.strftime('%m%d%Y_%H%M')
#     output_file = f"{output_nc_to_csv}/PREC_{time_str}.csv"
#     ouileut_fidw = ""
    
#     # Simpan data ke CSV
#     filtered_df[['y', 'x', 'time', 'z']].to_csv(output_file, index=False)
#     print(f"Data berhasil disimpan di {output_file}")

# ========================================================= csv to idw fix | no accumulation ========================================================= 

# import os
# import netCDF4 as nc
# import pandas as pd
# import numpy as np
# import cftime
# from datetime import datetime
# from scipy.spatial import cKDTree
# import rasterio
# from rasterio.transform import from_origin

# os.environ["PROJ_LIB"] = "C:/Users/2ndba/anaconda3/Library/share/proj"

# # Fungsi untuk interpolasi IDW
# def idw_interpolasi(x, y, z, xi, yi, power=2):
#     # Membuat pohon KD untuk mencari titik terdekat
#     pohon = cKDTree(np.array(list(zip(x, y))))
#     dist, idx = pohon.query(np.array(list(zip(xi.ravel(), yi.ravel()))), k=10)
#     bobot = 1 / dist**power
#     bobot /= bobot.sum(axis=1, keepdims=True)
#     zi = np.sum(z[idx] * bobot, axis=1)
#     return zi.reshape(xi.shape)

# file_path = "repository/input/data_raster/ECMWF.0125.202410311200.PREC.nc"
# output_nc_to_csv = "repository/output/hours/nc_to_csv"
# output_csv_to_idw = "repository/output/hours/csv_to_idw"

# # Buka file NetCDF
# dataset = nc.Dataset(file_path)

# # Ambil data dari dataset
# latitudes = dataset.variables['lat'][:]
# longitudes = dataset.variables['lon'][:]
# times = dataset.variables['time'][:]
# rainfall = dataset.variables['tp'][:]

# # Konversi waktu menggunakan UTC
# time_units = dataset.variables['time'].units
# time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'

# # Konversi waktu dengan memastikan hasil adalah datetime
# time_converted = nc.num2date(times, units=time_units, calendar=time_calendar)

# # Pastikan semua elemen dikonversi menjadi datetime
# time_converted_utc = []
# for time_value in time_converted:
#     if isinstance(time_value, cftime.datetime):  # Jika tipe cftime
#         time_value = datetime(
#             time_value.year, time_value.month, time_value.day,
#             time_value.hour, time_value.minute, time_value.second
#         )
#     time_converted_utc.append(time_value)

# # Konversi ke Pandas Timestamp dan tambahkan zona waktu UTC
# time_converted_utc = pd.to_datetime(time_converted_utc).tz_localize('UTC')

# # Ubah waktu menjadi data per 3 jam
# time_converted_3hr = time_converted_utc.round('3H')

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

# # Loop melalui setiap waktu unik untuk menyimpan data ke CSV dan melakukan IDW interpolasi
# unique_times = df['time'].unique()

# for unique_time in unique_times:
#     # Filter data berdasarkan waktu, dan buat salinan eksplisit
#     filtered_df = df[df['time'] == unique_time].copy()
    
#     # Hapus informasi zona waktu dari kolom 'time'
#     filtered_df['time'] = filtered_df['time'].dt.tz_localize(None)
    
#     # Buat nama file berdasarkan bulan, hari, tahun, dan jam untuk CSV
#     time_str = unique_time.strftime('%m%d%Y_%H%M')
#     output_file = f"{output_nc_to_csv}/PREC_{time_str}.csv"
    
#     # Simpan data ke CSV
#     filtered_df[['y', 'x', 'time', 'z']].to_csv(output_file, index=False)
#     print(f"Data berhasil disimpan di {output_file}")
    
#     # Ambil koordinat (x, y) dan nilai (z) dari filtered_df untuk interpolasi IDW
#     x = filtered_df['x'].values
#     y = filtered_df['y'].values
#     z = filtered_df['z'].values

#     # Tentukan grid untuk interpolasi
#     xmin, xmax = x.min(), x.max()
#     ymin, ymax = y.min(), y.max()
#     res = 0.092  # Resolusi dalam derajat, sesuaikan jika diperlukan

#     # Membuat grid hanya dalam rentang data
#     grid_x, grid_y = np.meshgrid(np.arange(xmin, xmax + res, res), np.arange(ymin, ymax + res, res))

#     # Interpolasi menggunakan IDW
#     grid_z = idw_interpolasi(x, y, z, grid_x, grid_y)

#     # Simpan hasil interpolasi ke GeoTIFF
#     output_tiff = f"{output_csv_to_idw}/PREC_{time_str}.tiff"
#     transformasi = from_origin(xmin, ymax, res, res)

#     # Gunakan CRS eksplisit jika EPSG bermasalah
#     crs = rasterio.crs.CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs")

#     with rasterio.open(
#         output_tiff,
#         'w',
#         driver='GTiff',
#         height=grid_z.shape[0],
#         width=grid_z.shape[1],
#         count=1,
#         dtype=grid_z.dtype,
#         crs=crs,
#         transform=transformasi,
#     ) as dst:
#         dst.write(grid_z, 1)

#     print(f"Hasil interpolasi disimpan di {output_tiff}")