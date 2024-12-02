import os
import netCDF4 as nc
import pandas as pd
import numpy as np
from netCDF4 import num2date

file_path = "repository/input/data_raster/ECMWF.0125.202410311200.PREC.nc"
output_dir = "repository/output/daily/nc_to_csv"

os.makedirs(output_dir, exist_ok=True)

data = nc.Dataset(file_path)
print(data)

latitude = data.variables["lat"][:]
longitude = data.variables["lon"][:]
times = data.variables["time"][:]
rainfall = data.variables["tp"][:] 

dates_utc = num2date(times, data.variables["time"].units)

print(dates_utc)

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