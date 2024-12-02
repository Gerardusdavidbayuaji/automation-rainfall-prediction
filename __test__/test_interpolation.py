import os
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import rasterio
from rasterio.transform import from_origin

# Pastikan jalur PROJ_LIB sudah benar
os.environ["PROJ_LIB"] = "C:/Users/2ndba/anaconda3/Library/share/proj"

# Fungsi untuk interpolasi IDW
def idw_interpolasi(x, y, z, xi, yi, power=2):
    # Membuat pohon KD untuk mencari titik terdekat
    pohon = cKDTree(np.array(list(zip(x, y))))
    dist, idx = pohon.query(np.array(list(zip(xi.ravel(), yi.ravel()))), k=10)
    bobot = 1 / dist**power
    bobot /= bobot.sum(axis=1, keepdims=True)
    zi = np.sum(z[idx] * bobot, axis=1)
    return zi.reshape(xi.shape)

# Folder input dan output
folder_input = "repository/output/nc_to_idw"
folder_output = "repository/output/idw/"
os.makedirs(folder_output, exist_ok=True)

# Membaca file CSV dari folder input
file_csv = [f for f in os.listdir(folder_input) if f.endswith('.csv')]

# Membuat grid untuk interpolasi berdasarkan batas koordinat
# left, top, right, bottom = 92.0, 9.0, 148.0, -14.0
left, top, right, bottom = 91.688545, 9.211264, 148.182665, -14.202865
resolusi = 0.05  # Resolusi grid dalam derajat
grid_x, grid_y = np.meshgrid(
    np.arange(left, right + resolusi, resolusi),  # Longitude
    np.arange(bottom, top + resolusi, resolusi)   # Latitude
)

# Memproses setiap file CSV
for file in file_csv:
    jalur_csv = os.path.join(folder_input, file)
    df = pd.read_csv(jalur_csv)

    # Ambil koordinat (x, y) dan nilai (z)
    x = df['x'].values
    y = df['y'].values
    z = df['z'].values

    # Interpolasi menggunakan IDW
    grid_z = idw_interpolasi(x, y, z, grid_x, grid_y)

    # Simpan hasil interpolasi ke GeoTIFF
    nama_output = os.path.join(folder_output, f"{os.path.splitext(file)[0]}.tiff")
    transformasi = from_origin(left, top, resolusi, -resolusi)  # Transformasi dengan resolusi baru

    # Gunakan CRS eksplisit jika EPSG bermasalah
    crs = rasterio.crs.CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs")
    
    with rasterio.open(
        nama_output,
        'w',
        driver='GTiff',
        height=grid_z.shape[0],
        width=grid_z.shape[1],
        count=1,
        dtype=grid_z.dtype,
        crs=crs,
        transform=transformasi,
    ) as dst:
        dst.write(grid_z, 1)

    print(f"Hasil interpolasi disimpan di {nama_output}")