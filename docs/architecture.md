# Architecture

The application keeps a thin Streamlit UI (`/app.py`) and delegates processing logic to `satproc`.

## Package layout

- `satproc/io.py` – dataset loading and validation entry points.
- `satproc/metadata.py` – metadata summarization for UI display.
- `satproc/processing.py` – wavelength lookup, PCA, spectra extraction, stats.
- `satproc/corrections.py` – guarded radiometric scaling only when explicit coefficients exist.
- `satproc/indices.py` – normalized-difference index computation.
- `satproc/visualization.py` – display-ready stretching and RGB composites.
- `satproc/sensors/enmap.py` – EnMAP product-level detection, spectral image discovery, VNIR/SWIR merge, and wavelength parsing from HDR/XML.
- `satproc/sensors/sentinel2.py` / `landsat.py` – sensor wavelength references for future sensor-specific presets.

## Key scientific constraints

- No generic atmospheric/radiometric correction is applied unless product metadata provides required coefficients.
- NDWI currently uses a green/NIR definition when no sensor-specific rule is available.
