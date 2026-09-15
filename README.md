# Hyperspectral Satellite Processor

Short description:
A local web-based hyperspectral and multispectral satellite image processing application built with Python, Streamlit, Rasterio, NumPy, Matplotlib and scikit-learn.

All processing runs locally on your machine (no required cloud processing service).

## Overview

Hyperspectral Satellite Processor is intended for exploratory Earth-observation workflows, including:

- hyperspectral image inspection
- multispectral satellite imagery exploration
- metadata inspection
- individual band visualization
- spectral signature extraction
- RGB and false-color composites
- PCA
- normalized-difference spectral indices
- exploratory Earth-observation analysis

The tool currently supports:

- EnMAP
- Sentinel-2
- Landsat 8/9
- generic GeoTIFF
- ENVI BSQ
- ENVI BIL
- ENVI BIP
- JP2 where supported by Rasterio/GDAL

## Current Features

- GeoTIFF / TIFF loading
- JPEG2000 / JP2 loading
- ENVI BSQ/BIL/BIP + HDR loading
- multiband raster support
- EnMAP hyperspectral cube loading
- wavelength extraction from ENVI headers when available
- metadata inspection
- image dimensions
- CRS
- raster bounds
- datatype
- nodata inspection
- individual-band viewer
- percentile contrast stretching
- RGB / false-color composite generation
- spectral signature for a selected pixel
- wavelength-vs-pixel-value plots
- PCA visualization
- band statistics
- normalized-difference index calculation
- local-folder mode for large hyperspectral datasets
- Streamlit local browser interface

## Current EnMAP Support

EnMAP products may contain files such as:

- `SPECTRAL_IMAGE.BSQ`
- `SPECTRAL_IMAGE.HDR`
- `METADATA.XML`
- `QL_PIXELMASK.TIF`
- `QL_QUALITY_CLOUD.TIF`
- `QL_QUALITY_CIRRUS.TIF`
- `QL_QUALITY_HAZE.TIF`
- `QL_QUALITY_SNOW.TIF`
- other quicklook and quality-mask files

Interpretation in this tool:

- `SPECTRAL_IMAGE.BSQ` = main hyperspectral science cube
- `SPECTRAL_IMAGE.HDR` = ENVI header describing dimensions/bands/wavelengths
- `METADATA.XML` = additional mission/product metadata
- `QL_*` files = quicklook, mask, or quality information

For very large BSQ files, use **Local folder/path** rather than uploading through the browser.

### EnMAP product levels (brief)

- **L1B**
  - calibrated sensor product / radiance-oriented processing
  - VNIR and SWIR may be separate cubes
- **L1C**
  - geometrically processed/orthorectified product
- **L2A**
  - atmospherically corrected surface-reflectance product
  - recommended for most spectral analysis, vegetation indices, material analysis, and classification

This software does not claim to perform all mission-specific correction chains automatically.

## Supported Satellite Data

| Mission / Format | Type | Recommended Product | Support |
| --- | --- | --- | --- |
| EnMAP | Hyperspectral | L2A | Supported / active development |
| Sentinel-2 | Multispectral | Level-2A | Basic raster support |
| Landsat 8/9 | Multispectral + Thermal | Collection 2 Level-2 | Basic raster support |
| Generic ENVI | Hyperspectral / Multiband | BSQ/BIL/BIP + HDR | Supported |
| Generic GeoTIFF | Raster | GeoTIFF | Supported |

## Satellite Data Sources

### EnMAP

Mission:
EnMAP hyperspectral Earth-observation mission

Official data access:
<https://www.enmap.org/data_access/>

Example data:
<https://www.enmap.org/data_tools/exampledata/>

Recommended for first hyperspectral testing: **EnMAP L2A**.

Typical files:

- `SPECTRAL_IMAGE.BSQ`
- `SPECTRAL_IMAGE.HDR`
- `METADATA.XML`

### Sentinel-2

Mission:
Copernicus Sentinel-2

Data source:
Copernicus Data Space Browser

<https://browser.dataspace.copernicus.eu/>

Recommended:
Sentinel-2 Level-2A surface reflectance.

The tool can currently work with individual raster bands and build RGB / false-color composites.

### Landsat 8/9

Data source:
USGS EarthExplorer

<https://earthexplorer.usgs.gov/>

Official Landsat access information:
<https://www.usgs.gov/landsat-missions/landsat-data-access>

Recommended:
Landsat Collection 2 Level-2.

## Quick Start

Recommended Python: **3.11 or 3.12**

### macOS / Linux

```bash
git clone https://github.com/VimsRocz/hyperspectral-satellite-processor.git
cd hyperspectral-satellite-processor

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

streamlit run app.py
```

Open:

<http://localhost:8501>

### Windows PowerShell

```powershell
git clone https://github.com/VimsRocz/hyperspectral-satellite-processor.git
cd hyperspectral-satellite-processor

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

streamlit run app.py
```

Open:

<http://localhost:8501>

## How to Test with EnMAP

1. Download an EnMAP L2A sample/product.
2. Extract the product folder locally.
3. Start the Streamlit application.
4. Select **Local folder/path**.
5. Paste the complete EnMAP L2A folder path.
6. In Raster, choose the file ending with `SPECTRAL_IMAGE.BSQ`.
7. Do not select `QL_PIXELMASK` or `QL_QUALITY` files for the main spectral analysis.
8. Open Dataset Inspector.
9. Confirm the hyperspectral band count and wavelength information.
10. Use Band Viewer.
11. Use Spectrum & PCA.
12. Select a pixel and plot its spectral signature.
13. Run PCA.
14. Use RGB / False Color or spectral indices where appropriate.

## Understanding the Workflow

```text
Satellite Product
    ↓
Product / File Identification
    ↓
Raster + Metadata Reading
    ↓
Band / Wavelength Inspection
    ↓
Band Visualization
    ↓
RGB / False Color
    ↓
Spectral Signature
    ↓
PCA / Spectral Indices
    ↓
Future Classification / Target Analysis
```

## Scientific Limitations

This tool must not blindly apply radiometric, atmospheric, or geometric correction.

Correct processing depends on:

- sensor
- product level
- calibration coefficients
- acquisition geometry
- solar geometry
- atmospheric parameters
- quality masks
- spectral response information

For scientific work, users should verify whether source products are radiance, TOA reflectance, or surface reflectance before interpreting results.

Do not assume scientific calibration unless the relevant processing chain is implemented and validated.

## Roadmap

- automatic EnMAP `METADATA.XML` parsing
- automatic L1B/L1C/L2A recognition
- automatic science-image vs quality-mask classification
- VNIR + SWIR handling
- wavelength-based band selection
- natural-color preset
- vegetation false-color preset
- SWIR presets
- NDVI
- NDWI
- red-edge indices
- automatic quality masking
- region-of-interest spectral averaging
- pixel-to-pixel spectral comparison
- spectral library comparison
- classification
- material / mineral analysis
- processed GeoTIFF export
- CSV spectral export
- Sentinel-2-specific adapter
- Landsat-specific adapter

## Project Structure

Current repository structure (core files):

- `app.py` — Streamlit user interface and workflow orchestration.
- `requirements.txt` — Python dependency list.
- `satproc/io.py` — raster input/loading utilities and related I/O helpers.
- `satproc/processing.py` — processing and analytics utilities (e.g., indices, PCA-related helpers).
- `satproc/corrections.py` — correction-framework utilities/placeholders for sensor-aware workflows.
- `DOWNLOAD_DATA.md` — additional notes on obtaining remote-sensing datasets.

## Large Data Files

Do not commit raw satellite imagery into GitHub.

Files such as:

- `*.bsq`
- `*.bil`
- `*.bip`
- `*.tif`
- `*.tiff`
- `*.jp2`

should remain local or be downloaded from official satellite archives.

Confirmed: `.gitignore` excludes these file patterns.

## Technology Stack

- Python
- Streamlit
- Rasterio / GDAL
- NumPy
- Pandas
- Matplotlib
- scikit-learn
- Pillow

## License

MIT License (see `LICENSE`).

## Contribution / Development Status

This project is under active development.

Issues and pull requests are welcome. Please note that this repository is not positioned as production-ready scientific processing software yet.
