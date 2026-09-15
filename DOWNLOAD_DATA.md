# Suggested data for testing

## 1. Sentinel-2

Use Copernicus Data Space Browser:

https://browser.dataspace.copernicus.eu/

Typical use in this starter app:
- Load individual JP2/TIFF bands
- Build RGB from separate files
- Inspect metadata

## 2. Landsat

Use USGS EarthExplorer:

https://earthexplorer.usgs.gov/

Typical use:
- Load individual band GeoTIFFs
- Build RGB / false-color composites
- Calculate indices

## 3. EnMAP hyperspectral

See:

https://www.enmap.org/data_access/

Typical use:
- Load a multiband hyperspectral raster
- View individual bands
- Plot a pixel spectrum
- Run PCA
- Calculate band-pair indices

## Notes

Choose processed products where possible (for example Level-2 surface
reflectance products) when you want analysis-ready data. Raw products may
require additional sensor-specific calibration and correction before
scientific interpretation.
