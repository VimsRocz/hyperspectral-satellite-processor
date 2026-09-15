# Satellite & Hyperspectral Post-Processor

A local, browser-based Python application for inspecting and exploring
satellite imagery.

## Current features

- GeoTIFF / TIFF
- JP2
- ENVI-compatible rasters readable by Rasterio
- Generic multiband imagery
- Sentinel-2 individual band files
- Landsat individual band files
- EnMAP / other hyperspectral multiband rasters
- Dataset metadata inspection
- Band visualization
- RGB and false-color composites
- Pixel spectral profile
- PCA visualization
- Generic normalized-difference indices
- Band statistics
- Framework for radiometric, atmospheric, and geometric correction

## Important scientific limitation

The app does NOT blindly apply atmospheric, radiometric, or geometric
corrections. Those depend on the sensor, processing level, calibration
metadata, geometry, and processing assumptions.

## Recommended Python

Python 3.11 or 3.12.

## Windows PowerShell

```powershell
cd satellite-postprocessor

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

streamlit run app.py
```

Open:

http://localhost:8501

## macOS / Linux

```bash
cd satellite-postprocessor

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

streamlit run app.py
```

Open:

http://localhost:8501

## Real satellite data

Useful public sources include:

- Copernicus Data Space Browser — Sentinel missions:
  https://browser.dataspace.copernicus.eu/
- USGS EarthExplorer — Landsat:
  https://earthexplorer.usgs.gov/
- EnMAP data portal / access information:
  https://www.enmap.org/data_access/

For a first hyperspectral test, use an EnMAP L2A scene if available to you.
