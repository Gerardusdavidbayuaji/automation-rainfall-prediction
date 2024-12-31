import rasterio
from rasterio.mask import mask
import geopandas as gpd

raster_path = "repository/output/daily/csv_to_idw/pch_day_01012025_0000.tif"
vector_path = "repository/input/data_vektor/pulau.geojson"
masking_save = "repository/output/__test__/masked_raster2.tif"

gdf = gpd.read_file(vector_path)

geometries = [geom for geom in gdf.geometry]

with rasterio.open(raster_path) as src:
    out_image, out_transform = mask(src, geometries, crop=True)
    out_meta = src.meta.copy()

out_meta.update({
    "driver": "GTiff",
    "height": out_image.shape[1],
    "width": out_image.shape[2],
    "transform": out_transform
})

# Menyimpan raster hasil masking
with rasterio.open(masking_save, "w", **out_meta) as dest:
    dest.write(out_image)