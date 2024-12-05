# import os
# import geopandas as gpd
# import requests


# # Fungsi untuk mengunggah file shapefile atau geotiff ke GeoServer
# def upload_to_geoserver(data_path, geoserver_endpoint, workspace, store):
#     file_extension = os.path.splitext(data_path)[1].lower()
#     if file_extension == ".shp":
#         file_type = "shp"
#         store_type = "datastores"
#     elif file_extension == ".tif":
#         file_type = "geotiff"
#         store_type = "coveragestores"
#     else:
#         print(f"Tipe file {file_extension} tidak didukung")
#         return None
    
#     # Format URL untuk upload file
#     absolute_path = os.path.abspath(data_path).replace("\\", "/")  # Pastikan jalur absolut
#     url = f"{geoserver_endpoint}/rest/workspaces/{workspace}/{store_type}/{store}/external.{file_type}"
#     print(f"URL upload: {url}")
    
#     # Header untuk GeoServer
#     headers = {"Content-type": "text/plain"}
#     response = requests.put(url, data=f"file://{absolute_path}", headers=headers, auth=("admin", "geoserver"))  # Tambahkan kredensial GeoServer
    
#     # Verifikasi hasil upload
#     if response.status_code in [200, 201]:
#         print(f"Berhasil upload data ke GeoServer: {data_path}")
#         return True
#     else:
#         print(f"Gagal upload data ke GeoServer: {data_path}. Status code: {response.status_code}")
#         print("Response:", response.text)
#         return False


# # Path untuk input dan output
# hours_input_folder = "repository/output/hours/clip/base"
# hours_result = "repository/output/hours/clip/result/pulau"
# balai_area = "repository/input/data_vektor/pulau.shp"

# # Endpoint dan workspace GeoServer
# geoserver_endpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"
# workspace = "demo_simadu"

# # Membaca shapefile balai
# balai_data = gpd.read_file(balai_area)

# # Pastikan CRS balai_data tetap dalam WGS84 (EPSG:4326)
# if balai_data.crs != "EPSG:4326":
#     balai_data = balai_data.to_crs("EPSG:4326")

# # Buat folder output jika belum ada
# os.makedirs(hours_result, exist_ok=True)

# # Loop untuk setiap file di folder input
# for file_name in os.listdir(hours_input_folder):
#     if file_name.endswith(".shp"):  # Proses hanya file shapefile
#         input_file_path = os.path.join(hours_input_folder, file_name)
#         output_file_name = f"PULAU_{os.path.splitext(file_name)[0]}.shp"
#         output_file_path = os.path.join(hours_result, output_file_name)
        
#         # Membaca shapefile input
#         prec_data = gpd.read_file(input_file_path)
        
#         # Pastikan CRS prec_data tetap dalam WGS84 (EPSG:4326)
#         if prec_data.crs != "EPSG:4326":
#             prec_data = prec_data.to_crs("EPSG:4326")
        
#         # Melakukan pemotongan (clip) pada data prec_data menggunakan geometri dari balai_data
#         clipped_prec_data = gpd.clip(prec_data, balai_data)
        
#         # Pastikan kolom 'grid_kl' berasal dari kolom 'class' di clipped_prec_data
#         clipped_prec_data['grid_kl'] = clipped_prec_data['class']
        
#         # Gabungkan data spasial menggunakan nearest join
#         merged_data = gpd.sjoin_nearest(clipped_prec_data, balai_data, how="left", rsuffix="_balai")
        
#         # Pilih kolom yang diinginkan dari data gabungan
#         merged_data = merged_data[['geometry', 'wilayah', 'kode_pulau', 'pulau', 'kode_prov', 'provinsi', 'kode_kk', 'kab_kota', 'grid_kl']]
        
#         # Tambahkan kolom baru untuk klasifikasi dan total
#         new_columns = [
#             'grid_kg', 'kelas_1', 'kelas_2', 'kelas_3', 'kelas_4', 'kelas_5',
#             'total_kl_1', 'total_kl_2', 'total_kl_3', 'total_kl_4', 'total_kl_5',
#             'total_kg_1', 'total_kg_2', 'total_kg_3', 'total_kg_4',
#         ]
#         for col in new_columns:
#             merged_data[col] = 0  # Inisialisasi nilai default
        
#         # Kalkulasi grid_kg berdasarkan grid_kl
#         def calculate_grid_kg(grid_kl):
#             if grid_kl in [1, 2]:
#                 return 1
#             elif grid_kl == 3:
#                 return 2
#             elif grid_kl == 4:
#                 return 3
#             elif grid_kl == 5:
#                 return 4
#             return 0
        
#         merged_data['grid_kg'] = merged_data['grid_kl'].apply(calculate_grid_kg)
        
#         # Perhitungan `kelas_1` hingga `kelas_5` berdasarkan `kode_pulau`
#         grouped = merged_data.groupby('kode_pulau')
        
#         for kode_pulau, group in grouped:
#             # Hitung jumlah kemunculan setiap nilai grid_kl dalam grup
#             grid_kl_counts = group['grid_kl'].value_counts().to_dict()
            
#             # Update nilai kelas berdasarkan grid_kl
#             merged_data.loc[merged_data['kode_pulau'] == kode_pulau, 'kelas_1'] = grid_kl_counts.get(1, 0)
#             merged_data.loc[merged_data['kode_pulau'] == kode_pulau, 'kelas_2'] = grid_kl_counts.get(2, 0)
#             merged_data.loc[merged_data['kode_pulau'] == kode_pulau, 'kelas_3'] = grid_kl_counts.get(3, 0)
#             merged_data.loc[merged_data['kode_pulau'] == kode_pulau, 'kelas_4'] = grid_kl_counts.get(4, 0)
#             merged_data.loc[merged_data['kode_pulau'] == kode_pulau, 'kelas_5'] = grid_kl_counts.get(5, 0)
        
#         # Perhitungan `total_kl_*` untuk seluruh dataset
#         grid_kl_counts_total = merged_data['grid_kl'].value_counts().to_dict()
#         merged_data['total_kl_1'] = grid_kl_counts_total.get(1, 0)
#         merged_data['total_kl_2'] = grid_kl_counts_total.get(2, 0)
#         merged_data['total_kl_3'] = grid_kl_counts_total.get(3, 0)
#         merged_data['total_kl_4'] = grid_kl_counts_total.get(4, 0)
#         merged_data['total_kl_5'] = grid_kl_counts_total.get(5, 0)
        
#         # Perhitungan `total_kg_*` untuk seluruh dataset
#         grid_kg_counts_total = merged_data['grid_kg'].value_counts().to_dict()
#         merged_data['total_kg_1'] = grid_kg_counts_total.get(1, 0)
#         merged_data['total_kg_2'] = grid_kg_counts_total.get(2, 0)
#         merged_data['total_kg_3'] = grid_kg_counts_total.get(3, 0)
#         merged_data['total_kg_4'] = grid_kg_counts_total.get(4, 0)
        
#         # Simpan hasil ke file shapefile baru
#         merged_data.to_file(output_file_path)
#         print(f"Proses selesai untuk file: {file_name}. Hasil disimpan di: {output_file_path}")

# # Proses unggah hasil ke GeoServer
# for shp_file in os.listdir(hours_result):
#     if shp_file.endswith(".shp"):
#         shp_path = os.path.normpath(os.path.join(hours_result, shp_file))
#         store_name = os.path.splitext(shp_file)[0]
#         if upload_to_geoserver(shp_path, geoserver_endpoint, workspace, store_name):
#             print(f"File Shapefile berhasil diunggah ke GeoServer: {shp_file}")
#         else:
#             print(f"Gagal mengunggah file Shapefile: {shp_file}")

# print("Semua file telah diproses dan diunggah ke GeoServer.")

# ====================================================== RASTER VALUE TO POINT CODE ======================================================

import geopandas as gpd
import rasterio
import numpy as np

interpolation_data = "repository/output/hours/csv_to_idw/PREC_12022024_1500.tif"
boundry_island_data = "repository/input/data_vektor/pulau_point.shp"
output_extracted_point_data = "repository/output/hours/clip/result/pulau/pulau_point_pch_7.shp"

# Baca shapefile
extract_point = gpd.read_file(boundry_island_data) 
print(extract_point)

# Buka file raster
with rasterio.open(interpolation_data) as src:
    raster_data = src.read(1)
    raster_transform = src.transform
    raster_crs = src.crs

# Ekstraksi nilai raster berdasarkan titik
extracted_values = [] 
for _, row in extract_point.iterrows():
    x, y = row.geometry.x, row.geometry.y 
    col_idx, row_idx = ~raster_transform * (x, y) 
    col_idx, row_idx = int(col_idx), int(row_idx)
    value = raster_data[row_idx, col_idx]
    extracted_values.append(value)

extract_point['value'] = extracted_values

# Klasifikasi curah hujan
def classify_grid_kl(val):
    if 0.00 <= val < 1.12:
        return 1
    elif 1.12 <= val < 2.81:
        return 2
    elif 2.81 <= val < 5.62:
        return 3
    elif 5.62 <= val < 8.43:
        return 4
    elif 8.43 <= val:
        return 5
    else:
        return 1

# Klasifikasi kesiapsiagaan bencana
def classify_grid_kg(val):
    if 0.00 <= val < 2.81:
        return 1
    elif 2.81 <= val < 4.21:
        return 2
    elif 4.21 <= val < 5.62:
        return 3
    elif 5.62 <= val:
        return 4
    else:
        return 1

# Tambahkan kolom klasifikasi
extract_point['grid_kl'] = extract_point['value'].apply(classify_grid_kl)
extract_point['grid_kg'] = extract_point['value'].apply(classify_grid_kg)

# Tambahkan kolom kelas
kelas_columns = ['kelas_1', 'kelas_2', 'kelas_3', 'kelas_4', 'kelas_5']
for col in kelas_columns:
    extract_point[col] = 0

# Perhitungan `kelas_1` hingga `kelas_5` berdasarkan `kode_pulau`
grouped = extract_point.groupby('kode_kk')

# Hapus duplikasi dan hanya ambil satu baris per `kode_kk`
extract_point = extract_point.drop_duplicates(subset='kode_kk', keep='first')

for kode_pulau, group in grouped:
    # Hitung jumlah kemunculan setiap nilai grid_kl dalam grup
    grid_kl_counts = group['grid_kl'].value_counts().to_dict()
            
    # Update nilai kelas berdasarkan grid_kl
    extract_point.loc[extract_point['kode_kk'] == kode_pulau, 'kelas_1'] = grid_kl_counts.get(1, 0)
    extract_point.loc[extract_point['kode_kk'] == kode_pulau, 'kelas_2'] = grid_kl_counts.get(2, 0)
    extract_point.loc[extract_point['kode_kk'] == kode_pulau, 'kelas_3'] = grid_kl_counts.get(3, 0)
    extract_point.loc[extract_point['kode_kk'] == kode_pulau, 'kelas_4'] = grid_kl_counts.get(4, 0)
    extract_point.loc[extract_point['kode_kk'] == kode_pulau, 'kelas_5'] = grid_kl_counts.get(5, 0)

# Hitung total untuk setiap kategori di grid_kl
grid_kl_counts_total = extract_point['grid_kl'].value_counts().to_dict()
extract_point['total_kl_1'] = grid_kl_counts_total.get(1, 0)
extract_point['total_kl_2'] = grid_kl_counts_total.get(2, 0)
extract_point['total_kl_3'] = grid_kl_counts_total.get(3, 0)
extract_point['total_kl_4'] = grid_kl_counts_total.get(4, 0)
extract_point['total_kl_5'] = grid_kl_counts_total.get(5, 0)

# Hitung total untuk setiap kategori di grid_kg
grid_kg_counts_total = extract_point['grid_kg'].value_counts().to_dict()
extract_point['total_kg_1'] = grid_kg_counts_total.get(1, 0)
extract_point['total_kg_2'] = grid_kg_counts_total.get(2, 0)
extract_point['total_kg_3'] = grid_kg_counts_total.get(3, 0)
extract_point['total_kg_4'] = grid_kg_counts_total.get(4, 0)

# Simpan ke shapefile
extract_point.to_file(output_extracted_point_data, driver="ESRI Shapefile")

print(f"Berhasil ekstrak data raster {output_extracted_point_data}")

