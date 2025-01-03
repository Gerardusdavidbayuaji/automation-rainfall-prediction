import os
import cftime
import ftplib
import datetime
import requests
import rasterio
import numpy as np
import pandas as pd
import netCDF4 as nc
import geopandas as gpd

from dotenv import load_dotenv
from scipy.spatial import cKDTree
from datetime import datetime as dt
from rasterio.transform import from_origin

load_dotenv()
os.environ["PROJ_LIB"] = "C:/Users/2ndba/anaconda3/Library/share/proj"

geoserver_endpoint = os.getenv("GEOSERVER_ENDPOINT")
workspace = os.getenv("WORKSPACE")

output_extracted_point_island_folder = "repository/output/hours/result/pulau"
output_extracted_point_balai_folder = "repository/output/hours/result/balai"
sampel_island_data = "repository/input/data_vektor/pch_pulau.geojson"
sampel_balai_data = "repository//input/data_vektor/pch_balai.geojson"
download_precipitation_path_raster = "repository/input/data_raster"
output_csv_to_idw = "repository/output/hours/csv_to_idw"
output_nc_to_csv = "repository/output/hours/nc_to_csv"

# konfigurasi ftp
ftp_host = os.getenv("HOST")
ftp_user = os.getenv("USER")
ftp_password = os.getenv("PASSWORD")
cycle = "12"
os.makedirs(download_precipitation_path_raster, exist_ok=True)

# FTP functions
def connect_ftp():
    ftp = ftplib.FTP(ftp_host)
    ftp.login(ftp_user, ftp_password)
    ftp.cwd("/")
    return ftp

def download_file_from_ftp(ftp, filename):
    try:
        file_list = ftp.nlst()
        if filename in file_list:
            local_file_path = os.path.join(download_precipitation_path_raster, filename)
            if not os.path.exists(local_file_path):
                with open(local_file_path, "wb") as local_file:
                    ftp.retrbinary(f"RETR {filename}", local_file.write)
                print(f"Berhasil download file {filename}")
            else:
                print(f"File {filename} sudah tersedia")
            return local_file_path
    except Exception:
        print("File rusak, tidak ada yang bisa dilakukan")
        return None

def download_latest_file_from_ftp(ftp):
    file_list = ftp.nlst()
    if file_list:
        latest_file = sorted(file_list)[-1]
        return download_file_from_ftp(ftp, latest_file)
    return None

# Download file .nc
today = datetime.date.today() - datetime.timedelta(days=1)
filename = f"ECMWF.0125.{today.strftime('%Y%m%d')}{cycle}00.PREC.nc"
print("Sedang mengunduh:", filename)

ftp = connect_ftp()
if ftp:
    local_file_path = download_file_from_ftp(ftp, filename) or download_latest_file_from_ftp(ftp)
    ftp.quit()
else:
    print("Tidak dapat terhubung ke server FTP.")

if local_file_path is None:
    print("File tidak tersedia untuk didownload")
    exit()

# Konversi ke UTC
def convert_time(times, time_units, time_calendar):
    time_converted = nc.num2date(times, units=time_units, calendar=time_calendar)
    time_converted_utc = []
    for time_value in time_converted:
        if isinstance(time_value, cftime.datetime):
            time_value = dt(
                time_value.year, time_value.month, time_value.day,
                time_value.hour, time_value.minute, time_value.second
            )
        time_converted_utc.append(time_value)
    return pd.to_datetime(time_converted_utc).tz_localize('UTC')

# Interval 3 jam => 04.00, 07.00, 10.00, 13.00, 16.00, 19.00, 22.00, 01.00
def three_hour_intervals(times):
    target_hours = [4, 7, 10, 13, 16, 19, 22, 1]
    adjested_times = []

    for time in times:
        hour_diff = [(abs((time.hour - h) % 24), h) for h in target_hours]
        closest_hour = min(hour_diff, key=lambda x: x[0])[1]

        if closest_hour == 1 and time.hour > 22:
            new_time = time + pd.Timedelta(days=1)
            new_time = new_time.replace(hour=closest_hour, minute=0, second=0, microsecond=0)
        else:
            new_time = time.replace(hour=closest_hour, minute=0, second=0, microsecond=0)

        adjested_times.append(new_time)

    return adjested_times

# Akumulasi curah hujan per 3 jam
def process_netcdf(local_file_path):
    print(f"Sedang membaca data {filename}")
    dataset = nc.Dataset(local_file_path)

    latitudes = dataset.variables['lat'][:]
    longitudes = dataset.variables['lon'][:]
    times = dataset.variables['time'][:]
    rainfall = dataset.variables['tp'][:]

    time_units = dataset.variables['time'].units
    time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'
    
    time_converted_utc = convert_time(times, time_units, time_calendar)
    time_converted_3hr = three_hour_intervals(time_converted_utc)

    data = []
    for time_index, time_value in enumerate(time_converted_3hr):
        for lat_index, lat in enumerate(latitudes):
            for lon_index, lon in enumerate(longitudes):
                rain_value = rainfall[time_index, 0, lat_index, lon_index]
                data.append([round(lat, 15), round(lon, 15), time_value, rain_value])

    df = pd.DataFrame(data, columns=['y', 'x', 'time', 'z'])

    df['Year'] = df['time'].dt.year
    df['Month'] = df['time'].dt.month
    df['Day'] = df['time'].dt.day
    df['Hour'] = df['time'].dt.hour

    df_accumulated = df.groupby(['Year', 'Month', 'Day', 'Hour', 'x', 'y'], as_index=False).agg({'time': 'first', 'z': 'sum'})

    return df_accumulated

# Ubah data nc menjadi csv, untuk dilanjutkan interpolasi IDW 
def save_to_csv(df_accumulated, output_nc_to_csv):
    unique_times = df_accumulated['time'].unique()

    for unique_time in unique_times:
        filtered_df = df_accumulated[df_accumulated['time'] == unique_time].copy()
        filtered_df['time'] = filtered_df['time'].dt.tz_localize(None)

        # Save as CSV
        time_str = unique_time.strftime('%m%d%Y_%H%M')
        output_file = f"{output_nc_to_csv}/pch_hour_{time_str}.csv"
        
        filtered_df[['y', 'x', 'time', 'z']].to_csv(output_file, index=False)
        print(f"Berhasil konversi nc untuk data tanggal {time_str}")
        
    return unique_times

# Interpolasi IDW
def idw_interpolation(x, y, z, xi, yi, power=2):
    tree = cKDTree(np.array(list(zip(x, y))))
    dist, idx = tree.query(np.array(list(zip(xi.ravel(), yi.ravel()))), k=10)
    weights = 1 / dist**power
    weights /= weights.sum(axis=1, keepdims=True)
    zi = np.sum(z[idx] * weights, axis=1)
    return zi.reshape(xi.shape)

# Upload data ke Geoserver
def upload_to_geoserver(data_path, store_name):
    file_extension = os.path.splitext(data_path)[1].lower()
    if file_extension == ".shp":
        file_type = "shp"
        store_type = "datastores"
    elif file_extension == ".tif":
        file_type = "geotiff"
        store_type = "coveragestores"
    
    absolute_path = os.path.abspath(data_path).replace("\\", "/")
    url = f"{geoserver_endpoint}/rest/workspaces/{workspace}/{store_type}/{store_name}/external.{file_type}"

    headers = {"Content-type": "text/plain"}
    response = requests.put(url, data=f"file://{absolute_path}", headers=headers)

    if response.status_code in [200, 201]:
        print(f"Berhasil upload {data_path} ke geoserver")
        return True
    else:
        print(f"Gagal upload {data_path} ke geoserver. Status code: {response.status_code}")
        return False

# Melakukan interpolasi, kemudian simpan hasil dengan format .tif
def interpolate_and_save_to_tiff(df_accumulated, output_csv_to_idw):
    unique_times = df_accumulated['time'].unique()

    for unique_time in unique_times:
        filtered_df = df_accumulated[df_accumulated['time'] == unique_time].copy()
        x = filtered_df['x'].values
        y = filtered_df['y'].values
        z = filtered_df['z'].values

        xmin, xmax = x.min(), x.max()
        ymin, ymax = y.min(), y.max()
        res = 0.092
        grid_x, grid_y = np.meshgrid(np.arange(xmin, xmax + res, res), np.arange(ymin, ymax + res, res))

        grid_z = idw_interpolation(x, y, z, grid_x, grid_y)

        time_str = unique_time.strftime('%m%d%Y_%H%M')
        output_tiff = f"{output_csv_to_idw}/pch_hour_{time_str}.tif"
        transformasi = from_origin(xmin, ymax, res, res)

        crs = rasterio.crs.CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs")
        with rasterio.open(output_tiff, 'w', driver='GTiff', height=grid_z.shape[0], width=grid_z.shape[1],
                           count=1, dtype=grid_z.dtype, crs=crs, transform=transformasi) as dst:
            dst.write(grid_z, 1)

        print(f"Berhasil melakukan interpolasi untuk data tanggal {time_str}")

        # Upload to GeoServer
        store_name = os.path.splitext(os.path.basename(output_tiff))[0]
        upload_to_geoserver(output_tiff, store_name)

# melakukan ekstrak data raster berdasarkan titik sampel
def process_extraction(boundary_data, raster_file, output_folder, prefix):
    extract_point = gpd.read_file(boundary_data)
    print(f"Melakukan ekstrak data raster {raster_file}")

    with rasterio.open(raster_file) as src:
        raster_data = src.read(1)
        raster_transform = src.transform

    # Ekstrak nilai raster berdasarkan titik
    extracted_values = []
    for _, row in extract_point.iterrows():
        x, y = row.geometry.x, row.geometry.y
        col_idx, row_idx = ~raster_transform * (x, y)
        col_idx, row_idx = int(col_idx), int(row_idx)
        value = raster_data[row_idx, col_idx]
        extracted_values.append(value)

    extract_point['value'] = extracted_values

    # Klasifikasi curah hujan dan kesiapsiagaan bencana
    # classify_grid_kl adalah klasifikasi curah hujan
    def classify_grid_kl(val):
        if 0.00 <= val < 1.12: #ringan
            return 1
        elif 1.12 <= val < 2.81: #sedang
            return 2
        elif 2.81 <= val < 5.62: # lebat
            return 3
        elif 5.62 <= val < 8.43: # sangat lebat
            return 4
        elif 8.43 <= val: # ekstrem
            return 5
        else:
            return 1
        
    # classify_grid_kg adalah klasifikasi kesiapsiagaan
    def classify_grid_kg(val):
        if 0.00 <= val < 2.81: #aman
            return 1
        elif 2.81 <= val < 4.21: #waspada
            return 2
        elif 4.21 <= val < 5.62: # siaga
            return 3
        elif 5.62 <= val: #awas
            return 4
        else:
            return 1

    # Tambahkan klasifikasi ke dataframe
    # grid_kl adalah nilai yang diperoleh dari ekstrak data raster (value) dengan titik menggunakan klasifikasi curah hujan
    # grid_kg adalah nilai yang diperoleh dari ekstrak data raster (value) dengan titik menggunakan klasifikasi curah hujan
    extract_point['grid_kl'] = extract_point['value'].apply(classify_grid_kl)
    extract_point['grid_kg'] = extract_point['value'].apply(classify_grid_kg)

    # Hitung total_kl_* dan total_kg_* untuk setiap kategori per wilayah
    # Kolom total_kl_* digunakan untuk mengisi nilai pada UI klasifikasi hujan
    # Kolom total_kg_* digunakan untuk mengisi nilai pada UI kesiapsiagaan
    # Operasi grid_kl_counts_total berfungsi untuk mengisi kolom total_kl_1 sampai total_kl_5 berdasarkan nilai jumlah kelas
    if 'wilayah' in extract_point.columns:
        grouped_pulau = extract_point.groupby('wilayah')
        for wilayah, group in grouped_pulau:
            grid_kl_counts = group['grid_kl'].value_counts().to_dict()
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kl_1'] = grid_kl_counts.get(1, 0)
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kl_2'] = grid_kl_counts.get(2, 0)
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kl_3'] = grid_kl_counts.get(3, 0)
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kl_4'] = grid_kl_counts.get(4, 0)
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kl_5'] = grid_kl_counts.get(5, 0)

    # kelas_kg_* diperoleh berdasarkan kumpulan grid_kg per wilayah
    if 'wilayah' in extract_point.columns:
        grouped_pulau = extract_point.groupby('wilayah')
        for wilayah, group in grouped_pulau:
            grid_kl_counts = group['grid_kg'].value_counts().to_dict()
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kg_1'] = grid_kl_counts.get(1, 0)
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kg_2'] = grid_kl_counts.get(2, 0)
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kg_3'] = grid_kl_counts.get(3, 0)
            extract_point.loc[extract_point['wilayah'] == wilayah, 'total_kg_4'] = grid_kl_counts.get(4, 0)

    # Output Pulau
    # kelas_kl_* diperoleh berdasarkan kumpulan grid_kl per kode_pulau
    if 'kode_pulau' in extract_point.columns:
        grouped_pulau = extract_point.groupby('kode_pulau')
        for kode_pulau, group in grouped_pulau:
            grid_kl_counts = group['grid_kl'].value_counts().to_dict()
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kl_1'] = grid_kl_counts.get(1, 0)
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kl_2'] = grid_kl_counts.get(2, 0)
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kl_3'] = grid_kl_counts.get(3, 0)
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kl_4'] = grid_kl_counts.get(4, 0)
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kl_5'] = grid_kl_counts.get(5, 0)

    # kelas_kg_* diperoleh berdasarkan kumpulan grid_kg per kode_pulau
    if 'kode_pulau' in extract_point.columns:
        grouped_pulau = extract_point.groupby('kode_pulau')
        for kode_pulau, group in grouped_pulau:
            grid_kl_counts = group['grid_kg'].value_counts().to_dict()
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kg_1'] = grid_kl_counts.get(1, 0)
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kg_2'] = grid_kl_counts.get(2, 0)
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kg_3'] = grid_kl_counts.get(3, 0)
            extract_point.loc[extract_point['kode_pulau'] == kode_pulau, 'kelas_kg_4'] = grid_kl_counts.get(4, 0)

        # tampilkan nilai tertinggi saja berdasarkan value, karena acuannya menggunakan nilai tertinggi pada masing-masing pulau
        extract_point = extract_point.loc[extract_point.groupby('kode_pulau')['value'].idxmax()]
        # Hapus kolom grid_kl dan grid_kg, karena sudah tidak digunakan lagi untuk pedoman perhitungan
        extract_point = extract_point.drop(columns=['grid_kl', 'grid_kg'])


    # Output Balai
    # kelas_kl_* diperoleh berdasarkan kumpulan grid_kl per kode_balai
    if 'kode_balai' in extract_point.columns:
        grouped_balai = extract_point.groupby('kode_balai')
        for kode_balai, group in grouped_balai:
            grid_kg_counts = group['grid_kl'].value_counts().to_dict()
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kl_1'] = grid_kg_counts.get(1, 0)
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kl_2'] = grid_kg_counts.get(2, 0)
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kl_3'] = grid_kg_counts.get(3, 0)
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kl_4'] = grid_kg_counts.get(4, 0)
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kl_5'] = grid_kg_counts.get(4, 0)

    # kelas_kg_* diperoleh berdasarkan kumpulan grid_kg per kode_balai
    if 'kode_balai' in extract_point.columns:
        grouped_balai = extract_point.groupby('kode_balai')
        for kode_balai, group in grouped_balai:
            grid_kg_counts = group['grid_kg'].value_counts().to_dict()
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kg_1'] = grid_kg_counts.get(1, 0)
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kg_2'] = grid_kg_counts.get(2, 0)
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kg_3'] = grid_kg_counts.get(3, 0)
            extract_point.loc[extract_point['kode_balai'] == kode_balai, 'kelas_kg_4'] = grid_kg_counts.get(4, 0)

        # Tampilkan nilai tertinggi saja berdasarkan value, karena acuannya menggunakan nilai tertinggi pada masing-masing balai
        extract_point = extract_point.loc[extract_point.groupby('kode_balai')['value'].idxmax()]
        # Hapus kolom grid_kl dan grid_kg, karena sudah tidak digunakan lagi untuk pedoman perhitungan
        extract_point = extract_point.drop(columns=['grid_kl', 'grid_kg'])

    extract_point['last_data'] = filename
    current_time = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    extract_point['last_updt'] = current_time

    # Simpan ke shapefile
    output_file = os.path.join(output_folder, f"{prefix}_{os.path.basename(raster_file).replace('.tif', '.shp')}")
    extract_point.to_file(output_file, driver="ESRI Shapefile")
    print(f"Berhasil ekstrak data {output_file}")

    # Upload ke GeoServer
    store_name = os.path.splitext(os.path.basename(output_file))[0]
    upload_to_geoserver(output_file, store_name)


# Looping data .tif pada folder
for tif_file in os.listdir(output_csv_to_idw):
    if tif_file.endswith('.tif'):
        raster_path = os.path.join(output_csv_to_idw, tif_file)

        # Proses data pulau
        process_extraction(sampel_island_data, raster_path, output_extracted_point_island_folder, "pulau")
        
        # Proses data balai
        process_extraction(sampel_balai_data, raster_path, output_extracted_point_balai_folder, "balai")

def process_netcdf_and_interpolate_with_extraction(
    local_file_path, 
    output_nc_to_csv, 
    output_csv_to_idw, 
    sampel_island_data, 
    sampel_balai_data, 
    output_extracted_point_island_folder, 
    output_extracted_point_balai_folder
):
    # Langkah 1: Proses NetCDF dan Simpan CSV
    df_accumulated = process_netcdf(local_file_path)
    save_to_csv(df_accumulated, output_nc_to_csv)
    
    # Langkah 2: Interpolasi dan Simpan GeoTIFF
    interpolate_and_save_to_tiff(df_accumulated, output_csv_to_idw)
    
    # Langkah 3: Ekstraksi Data Raster untuk Setiap File GeoTIFF
    for tif_file in os.listdir(output_csv_to_idw):
        if tif_file.endswith('.tif'):
            raster_path = os.path.join(output_csv_to_idw, tif_file)
            
            # Proses data pulau
            process_extraction(sampel_island_data, raster_path, output_extracted_point_island_folder, "pulau")
            
            # Proses data balai
            process_extraction(sampel_balai_data, raster_path, output_extracted_point_balai_folder, "balai")

process_netcdf_and_interpolate_with_extraction(
    local_file_path, 
    output_nc_to_csv, 
    output_csv_to_idw,  
    sampel_island_data, 
    sampel_balai_data, 
    output_extracted_point_island_folder, 
    output_extracted_point_balai_folder
)