from rasterio.transform import from_origin
from datetime import datetime as dt
from scipy.spatial import cKDTree
from dotenv import load_dotenv
import geopandas as gpd
import netCDF4 as nc
import pandas as pd
import numpy as np
import rasterio
import requests
import datetime
import ftplib
import cftime
import os

load_dotenv()
os.environ["PROJ_LIB"] = "C:/Users/2ndba/anaconda3/Library/share/proj"

geoserver_endpoint = os.getenv("GEOSERVER_ENDPOINT")
workspace = os.getenv("WORKSPACE")

download_precipitation_path_raster = "repository/input/data_raster/rch"
output_csv_to_idw = "repository/output/rch/csv_to_idw"
output_nc_to_csv = "repository/output/rch/nc_to_csv"

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

# Akumulasi curah hujan harian
def process_netcdf(local_file_path):
    dataset = nc.Dataset(local_file_path)

    latitudes = dataset.variables['lat'][:]
    longitudes = dataset.variables['lon'][:]
    times = dataset.variables['time'][:]
    rainfall = dataset.variables['tp'][:]

    time_units = dataset.variables['time'].units
    time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'
    
    time_converted_utc = convert_time(times, time_units, time_calendar)
    time_converted_10min = time_converted_utc.round('10min')

    print(f"Rentang waktu data: {time_converted_utc.min()} hingga {time_converted_utc.max()}")

    data = []
    for time_index, time_value in enumerate(time_converted_10min):
        for lat_index, lat in enumerate(latitudes):
            for lon_index, lon in enumerate(longitudes):
                rain_value = rainfall[time_index, 0, lat_index, lon_index]
                data.append([round(lat, 15), round(lon, 15), time_value, rain_value])

    df = pd.DataFrame(data, columns=['y', 'x', 'time', 'z'])

    df_10min = df.groupby(['time', 'x', 'y'], as_index=False).agg({
        'z': 'sum'
    })

    df_10min['Year'] = df_10min['time'].dt.year
    df_10min['Month'] = df_10min['time'].dt.month
    df_10min['Day'] = df_10min['time'].dt.day
    df_10min['Hour'] = df_10min['time'].dt.hour
    df_10min['Minute'] = df_10min['time'].dt.minute

    return df_10min

def save_today_to_csv(df_10min, output_nc_to_csv):
    # Dapatkan tanggal hari ini dalam UTC
    today_utc = pd.Timestamp.now(tz='UTC').floor('D')
    print(f"Filter data untuk tanggal (UTC): {today_utc}")
    
    # Filter df_10min untuk data dengan tanggal yang sama dengan hari ini
    df_today = df_10min[df_10min['time'].dt.floor('D') == today_utc]
    
    if df_today.empty:
        print(f"Tidak ada data untuk hari ini (UTC: {today_utc}).")
        return []

    # Simpan per 10 menit
    unique_times = df_today['time'].unique()
    for unique_time in unique_times:
        # Filter data berdasarkan waktu unik
        filtered_df = df_today[df_today['time'] == unique_time].copy()
        filtered_df['time'] = filtered_df['time'].dt.tz_localize(None)

        # Format waktu sebagai string untuk nama file
        time_str = unique_time.strftime('%m%d%Y_%H%M')
        output_file = f"{output_nc_to_csv}/rch_day_minute_{time_str}.csv"

        # Simpan data ke CSV
        filtered_df[['y', 'x', 'time', 'z']].to_csv(output_file, index=False)
        print(f"Data berhasil disimpan di {output_file}")

    return unique_times

if __name__ == "__main__":
    # Unduh file .nc dari FTP
    ftp = connect_ftp()
    if ftp:
        local_file_path = download_file_from_ftp(ftp, filename) or download_latest_file_from_ftp(ftp)
        ftp.quit()
    else:
        print("Tidak dapat terhubung ke server FTP.")
        exit()

    if local_file_path is None:
        print("File tidak tersedia untuk didownload")
        exit()

    # Proses file .nc
    print("Memproses file .nc...")
    df_10min = process_netcdf(local_file_path)

    # Simpan data ke CSV
    print("Menyimpan data ke CSV...")
    unique_times = save_today_to_csv(df_10min, output_nc_to_csv)