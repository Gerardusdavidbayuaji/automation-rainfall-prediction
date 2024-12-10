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

# load_dotenv()
# os.environ["PROJ_LIB"] = "C:/Users/2ndba/anaconda3/Library/share/proj"

# geoserver_endpoint = os.getenv("GEOSERVER_ENDPOINT")
# workspace = os.getenv("WORKSPACE")

# output_extracted_point_island_folder = "repository/output/pch/hours/result/balai"
# output_extracted_point_balai_folder = "repository/output/hours/result/balai"
# boundry_island_data = "repository/input/data_vektor/sampel_pch_pulaui.shp"
# boundry_balai_data = "repository/input/data_vektor/sampel_pch_balai.shp"
# download_precipitation_path_raster = "repository/input/data_raster/rch"
# output_csv_to_idw = "repository/output/pch/hours/csv_to_idw"
# output_nc_to_csv = "repository/output/pch/hours/nc_to_csv"

# # konfigurasi ftp
# ftp_host = os.getenv("HOST_RCH")
# ftp_user = os.getenv("USER_RCH")
# ftp_password = os.getenv("PASSWORD_RCH")
# os.makedirs(download_precipitation_path_raster, exist_ok=True)

# def connect_ftp():
#     ftp = ftplib.FTP(ftp_host)
#     ftp.login(ftp_user, ftp_password)
#     ftp.cwd("/netcdf")
#     return ftp

# def download_file_from_ftp(ftp, filename):
#     file_list = ftp.nlst()
#     if filename in file_list:
#         local_file_path = os.path.join(download_precipitation_path_raster, filename)
#         if not os.path.exists(local_file_path):
#             with open(local_file_path, "wb") as local_file:
#                 ftp.retrbinary(f"RETR {filename}", local_file.write)
#             print(f"Berhasil download file {filename}")
#         else:
#             print(f"File {filename} sudah tersedia")
#         return local_file_path
#     return None

# def download_latest_file_from_ftp(ftp):
#     file_list = ftp.nlst()
#     if file_list:
#         latest_file = sorted(file_list)[-1]
#         return download_file_from_ftp(ftp, latest_file)
#     return None

# # Download file .nc
# today = datetime.date.today() - datetime.timedelta(days=1)
# filename = f"Prec_{today.strftime('%Y%m%d')}0000.nc"
# print("Sedang mengunduh:", filename)

# ftp = connect_ftp()
# if ftp:
#     local_file_path = download_file_from_ftp(ftp, filename) or download_latest_file_from_ftp(ftp)
#     ftp.quit()
# else:
#     print("Tidak dapat terhubung ke server FTP.")

# if local_file_path is None:
#     print("File tidak tersedia untuk didownload")
#     exit()

read_data = "repository/input/data_raster/rch/Prec_202412090000.nc"
dataset = nc.Dataset(read_data, mode='r')
print("cek nc", dataset)