# hyperspectral-satellite-processor

Local Streamlit app for hyperspectral and multispectral raster exploration (offline workflow).

## Features

- GeoTIFF / JP2 / ENVI-style raster loading
- EnMAP detection (L1B/L1C/L2A), SPECTRAL_IMAGE auto-discovery, VNIR/SWIR merge
- Wavelength-aware band lookup and presets
- Metadata inspection, RGB/false color, NDVI/NDWI/red-edge/SWIR views
- Pixel spectral signature plotting, PCA visualization, per-band statistics

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- Provide a local file path (or EnMAP product directory) in the sidebar.
- Large satellite files are intentionally excluded from version control.
- Atmospheric/radiometric correction is not applied unless explicit coefficients exist in metadata.
