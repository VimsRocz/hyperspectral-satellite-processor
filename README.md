# Hyperspectral Satellite Processor

A local, browser-based Python application for inspecting, visualizing, and exploring hyperspectral and multispectral Earth-observation imagery.

The processing runs on the user's own computer. Large satellite products can be opened directly from a local folder without uploading them to a cloud service.

## What the tool does

The application provides a sensor-aware workflow for:

- GeoTIFF, JP2, ENVI BSQ/BIL/BIP raster ingestion
- EnMAP hyperspectral data
- Sentinel-2 raster products
- Landsat 8/9 raster products
- raster metadata inspection
- wavelength-aware band browsing
- RGB and false-color composites
- pixel and ROI spectral profiles
- PCA visualization
- generic normalized-difference indices
- wavelength-aware NDVI, NDWI, NDMI, and red-edge NDVI presets
- band statistics
- downloadable spectral CSV output

The project is intended for exploratory analysis and software development. It is not a replacement for validated mission-specific scientific processing chains.

## Supported sensors and formats

| Sensor / Format | Type | Recommended Product | Current Support |
| --- | --- | --- | --- |
| EnMAP | Hyperspectral | L2A | Advanced / active development |
| Sentinel-2 | Multispectral | Level-2A | Basic / developing |
| Landsat 8/9 | Multispectral + Thermal | Collection 2 Level-2 | Basic / developing |
| Generic ENVI | Hyperspectral / multiband | BSQ/BIL/BIP + HDR | Supported |
| Generic GeoTIFF | Raster | GeoTIFF | Supported |
| JP2 | Raster | Product-dependent | Supported where Rasterio/GDAL supports the file |

## Sensor & Product tab

The application now includes a **Sensor & Product** view that explains:

- detected sensor
- mission name
- detected product level
- selected file role
- data quantity where known
- recommended product level
- official mission website
- official data access link
- documentation/example-data link

The application also warns when a user selects a quality mask or quicklook instead of a science image.

## EnMAP

Official mission:

https://www.enmap.org/

Official data access:

https://www.enmap.org/data_access/

Example data:

https://www.enmap.org/data_tools/exampledata/

Typical EnMAP product files include:

- `SPECTRAL_IMAGE.BSQ`
- `SPECTRAL_IMAGE.HDR`
- `SPECTRAL_IMAGE_VNIR.BSQ`
- `SPECTRAL_IMAGE_SWIR.BSQ`
- `METADATA.XML`
- `QL_PIXELMASK*.TIF`
- `QL_QUALITY_*.TIF`
- `QL_VNIR.TIF`
- `QL_SWIR.TIF`

The software classifies them approximately as:

- `SPECTRAL_IMAGE*` → science image
- `QL_PIXELMASK*` / `QL_QUALITY_*` → quality mask
- `QL_VNIR` / `QL_SWIR` → quicklook

### EnMAP product levels

**L1B**
- radiometrically calibrated / radiance-oriented product
- VNIR and SWIR may be delivered as separate cubes
- do not interpret it as surface reflectance

**L1C**
- geometrically corrected / orthorectified radiance-oriented product

**L2A**
- atmospherically corrected surface-reflectance product
- recommended in this application for most spectral signatures, vegetation indices, material analysis, and later classification workflows

## Sentinel-2

Official mission:

https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-2

Copernicus Data Space Browser:

https://browser.dataspace.copernicus.eu/

Recommended starting point:

**Sentinel-2 Level-2A**

The application currently supports generic raster/band workflows. Individual Sentinel-2 band files can be used even when the product is not stored as one multiband raster.

## Landsat 8/9

Official mission:

https://www.usgs.gov/landsat-missions

USGS EarthExplorer:

https://earthexplorer.usgs.gov/

Data access information:

https://www.usgs.gov/landsat-missions/landsat-data-access

Recommended starting point:

**Landsat Collection 2 Level-2**

Landsat contains reflectance-oriented optical bands and thermal products. Thermal bands should not be interpreted as reflectance bands.

## Performance architecture

The application is optimized for interactive Streamlit use.

### Cached work

The UI caches deterministic results using `st.cache_data`, including:

- raster discovery
- raster metadata
- band labels
- wavelengths
- downsampled band previews
- RGB composites
- band statistics
- normalized-difference results
- PCA results

Cache keys include normalized paths and file/directory signatures so that modified files can invalidate cached results.

### Raster discovery

Science images are prioritized ahead of masks/quicklooks.

The scan filters by supported raster extensions before asking GDAL/Rasterio to open a file.

### PCA

PCA remains a preview operation rather than a full-resolution transform.

The workflow:

1. reads a downsampled float32 cube
2. finds valid pixels
3. samples at most a configurable number of pixels for fitting
4. fits three PCA components
5. transforms the valid preview in chunks
6. stretches PC1/PC2/PC3 for visualization

This reduces peak memory compared with fitting every valid pixel.

### RGB and indices

Three bands from the same raster are read in one Rasterio call where practical.

Normalized-difference indices read both requested bands together and operate in float32.

## Automatic wavelength presets

When wavelength metadata is available, the application finds the nearest real band to target wavelengths.

Supported presets include:

- Natural Color
- Vegetation False Color
- SWIR False Color
- NDVI
- NDWI
- NDMI
- Red-edge NDVI

The UI shows both the selected band number and the actual wavelength used.

## Spectral profiles

The Spectrum tab supports:

- a single-pixel spectrum
- a square ROI mean spectrum using a user-defined pixel radius
- wavelength-aware x-axis when wavelength metadata exists
- product-aware y-axis label where the data quantity is known
- CSV export

## Scientific limitations

This software does **not** silently apply mission-specific:

- radiometric correction
- atmospheric correction
- geometric correction
- orthorectification
- quality masking

Correct scientific processing depends on factors including:

- sensor
- product level
- calibration coefficients
- acquisition geometry
- solar geometry
- atmospheric parameters
- quality masks
- spectral response information

Before interpreting a spectrum, verify whether the source product represents:

- raw digital numbers
- radiance
- top-of-atmosphere reflectance
- surface reflectance
- brightness temperature / thermal science data

The tool deliberately keeps scientific assumptions visible rather than pretending every raster is analysis-ready.

## Quick start

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

http://localhost:8501

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

## Recommended EnMAP workflow

1. Download and extract an EnMAP L2A product.
2. Start the Streamlit app.
3. Choose **Local folder/path**.
4. Paste the complete EnMAP product folder path.
5. Choose the raster ending in `SPECTRAL_IMAGE.BSQ`.
6. Open **Sensor & Product** and confirm the detected product.
7. Open **Dataset Inspector** and verify wavelength metadata.
8. Use **Band Viewer**.
9. Create **Natural Color** or another wavelength-based composite.
10. Plot a pixel/ROI spectrum.
11. Run PCA.
12. Try NDVI/NDWI/NDMI when the required wavelengths are covered.

For very large BSQ files, local-folder mode is preferred over browser upload.

## Large data guidance

Do not commit satellite imagery into GitHub.

The repository ignores common large raster formats such as:

- `*.bsq`
- `*.bil`
- `*.bip`
- `*.tif`
- `*.tiff`
- `*.jp2`

It also ignores common local data folders:

- `data/`
- `datasets/`
- `temp/`

## Project structure

```text
app.py
satproc/
  __init__.py
  io.py
  metadata.py
  processing.py
  indices.py
  corrections.py
  sensors/
    __init__.py
    base.py
    enmap.py
    sentinel2.py
    landsat.py
tests/
  test_metadata.py
  test_indices.py
requirements.txt
README.md
.gitignore
```

## Testing

Run:

```bash
python -m compileall .
pytest -q
```

Then launch:

```bash
streamlit run app.py
```

## Technology stack

- Python
- Streamlit
- Rasterio / GDAL
- NumPy
- Pandas
- Matplotlib
- scikit-learn
- Pillow
- pytest

## Roadmap

Next priorities include:

- richer EnMAP `METADATA.XML` parsing
- FWHM extraction
- automatic quality-mask application
- stronger Sentinel-2 product adapters
- stronger Landsat product adapters
- VNIR + SWIR product-aware workflows
- interactive map/ROI selection
- spectral-library comparison
- classification
- material/mineral workflows
- GeoTIFF export
- richer CSV/export metadata
- profiling/performance diagnostics

## Development status

This project is under active development.

Issues and pull requests are welcome, but the repository should not yet be treated as production-certified scientific processing software.
