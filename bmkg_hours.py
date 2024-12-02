# =============================================================== nc > csv > tiff (interpolasi) ==============================================================

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

# # Akumulasi nilai 'z' (curah hujan) berdasarkan waktu (Year, Month, Day, Hour)
# df_accumulated = df.groupby(['Year', 'Month', 'Day', 'Hour', 'x', 'y'], as_index=False).agg({'time': 'first', 'z': 'sum'})

# # Loop melalui setiap waktu unik untuk menyimpan data ke CSV dan melakukan IDW interpolasi
# unique_times = df_accumulated['time'].unique()

# for unique_time in unique_times:
#     # Filter data berdasarkan waktu, dan buat salinan eksplisit
#     filtered_df = df_accumulated[df_accumulated['time'] == unique_time].copy()
    
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

# =============================================================== tiff > shp (reclassify) ==============================================================

# import os
# import numpy as np
# import rasterio
# import geopandas as gpd
# from rasterio.features import shapes
# from shapely.geometry import shape

# os.environ["PROJ_LIB"] = "C:/Users/2ndba/anaconda3/Library/share/proj"

# input_folder = "repository/output/hours/csv_to_idw"
# output_folder = "repository/output/hours/clip/balai/base"
# balai_area = "repository/input/data_vektor/balai.shp"

# os.makedirs(output_folder, exist_ok=True)

# # Melakukan reclassify
# def reclassify_raster(raster_array, bins, values):
#     """Reclassify array based on bins and corresponding values."""
#     classified = np.digitize(raster_array, bins, right=False)
#     classified = np.clip(classified, 1, len(values))
#     reclassified_array = np.vectorize(lambda x: values[x-1] if 1 <= x <= len(values) else 0)(classified)
#     return reclassified_array.astype('uint8')

# # Aturan reclassify
# bins = [0.02, 1.12, 2.81, 5.62, 8.43, np.inf]
# values = [1, 2, 3, 4, 5]

# # Ambil data tiff
# for tiff_file in os.listdir(input_folder):
#     if tiff_file.endswith(".tiff"):
#         input_path = os.path.join(input_folder, tiff_file)
#         output_shapefile = os.path.join(output_folder, f"{os.path.splitext(tiff_file)[0]}.shp")

#         with rasterio.open(input_path) as src:
#             raster_array = src.read(1)
#             affine = src.transform
#             crs = src.crs
            
#             # Lakukan reclassify
#             reclassified_array = reclassify_raster(raster_array, bins, values)
            
#             # Konversi raster ke vektor (poligon)
#             shapes_generator = shapes(reclassified_array, transform=affine)
#             polygons = []
#             classes = []
#             for geom, value in shapes_generator:
#                 if value != 0:  # Abaikan nilai nol
#                     polygons.append(shape(geom))
#                     classes.append(value)

#             # Simpan ke shapefile menggunakan GeoPandas
#             gdf = gpd.GeoDataFrame({"class": classes}, geometry=polygons, crs=crs)
#             gdf.to_file(output_shapefile)
#             print(f"Shapefile berhasil disimpan: {output_shapefile}")

# ============================================ clip balai > prec_data > struktur properties ===========================================


import geopandas as gpd
import os

# Path untuk input dan output
hours_input_folder = "repository/output/hours/clip/balai/base/"
hours_result = "repository/output/hours/clip/balai/result/"
balai_area = "repository/input/data_vektor/balai.shp"

# Membaca shapefile
prec_data = gpd.read_file(hours_input_folder)
balai_data = gpd.read_file(balai_area)

# Pastikan CRS tetap dalam WGS84 (EPSG:4326)
if prec_data.crs != "EPSG:4326":
    prec_data = prec_data.to_crs("EPSG:4326")
if balai_data.crs != "EPSG:4326":
    balai_data = balai_data.to_crs("EPSG:4326")

# Melakukan pemotongan (clip) pada data prec_data menggunakan geometri dari balai_data
clipped_prec_data = gpd.clip(prec_data, balai_data)

# Hitung jumlah kemunculan setiap nilai class (1-5) pada data prec_data yang sudah dipotong
class_counts = clipped_prec_data['class'].value_counts().to_dict()

# Gabungkan data spasial menggunakan nearest join
merged_data = gpd.sjoin_nearest(clipped_prec_data, balai_data, how="left", rsuffix="_balai")

# Pastikan kolom yang dibutuhkan ada di hasil join
print("Kolom hasil join:", merged_data.columns)

# Pilih kolom yang diinginkan dari data gabungan
merged_data = merged_data[['geometry', 'kode_balai', 'balai', 'wilayah', 'class']]

# Tambahkan kolom baru untuk klasifikasi dan total
new_columns = [
    'kelas_1', 'kelas_2', 'kelas_3', 'kelas_4', 'kelas_5',
    'total_1', 'total_2', 'total_3', 'total_4', 'total_5'
]

for col in new_columns:
    merged_data[col] = 0  # Inisialisasi nilai default

# Grupkan data berdasarkan kode_balai
grouped = merged_data.groupby('kode_balai')

# Proses setiap grup
for kode_balai, group in grouped:
    # Ambil array class dari grup saat ini
    class_array = group['class'].tolist()

    # Hitung jumlah kemunculan setiap nilai class (1-5) di dalam grup
    count_class = {i: class_array.count(i) for i in range(1, 6)}

    # Update nilai kelas untuk grup tersebut
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'kelas_1'] = count_class.get(1, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'kelas_2'] = count_class.get(2, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'kelas_3'] = count_class.get(3, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'kelas_4'] = count_class.get(4, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'kelas_5'] = count_class.get(5, 0)

    # Menggunakan nilai total yang dihitung sebelumnya pada seluruh data untuk mengisi 'total_1' - 'total_5'
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'total_1'] = class_counts.get(1, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'total_2'] = class_counts.get(2, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'total_3'] = class_counts.get(3, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'total_4'] = class_counts.get(4, 0)
    merged_data.loc[merged_data['kode_balai'] == kode_balai, 'total_5'] = class_counts.get(5, 0)

# Simpan hasil ke file shapefile baru
merged_data.to_file(hours_result)

print("Proses selesai. File telah disimpan di:", hours_result)