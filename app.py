from __future__ import annotations

import math
import pandas as pd
import streamlit as st

from satproc.indices import normalized_difference
from satproc.io import load_dataset
from satproc.metadata import summarize_metadata
from satproc.models import DatasetLoadError
from satproc.processing import band_index_from_wavelength, band_stats, extract_pixel_spectrum, pca_cube
from satproc.visualization import rgb_composite, stretch_to_uint8

st.set_page_config(page_title="Hyperspectral Satellite Processor", layout="wide")
st.title("Hyperspectral Satellite Processor")

st.sidebar.header("Input")
source_path = st.sidebar.text_input("Local file or EnMAP product directory", value="")

cube = None
if source_path:
    try:
        cube = load_dataset(source_path)
        st.success(f"Loaded: {cube.source_path}")
    except DatasetLoadError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Unexpected error while loading dataset: {exc}")

if cube is not None:
    presets = [
        "Natural RGB",
        "Vegetation false color",
        "NDVI",
        "NDWI",
        "Red-edge visualization",
        "SWIR composite",
        "PCA",
    ]

    tab_meta, tab_view, tab_spectrum, tab_stats = st.tabs(["Metadata", "Visualization", "Spectrum", "Band stats"])

    with tab_meta:
        st.json(summarize_metadata(cube), expanded=False)

    with tab_view:
        preset = st.selectbox("Preset", presets)

        def idx(w: float) -> int:
            return band_index_from_wavelength(cube.wavelengths_nm, w)

        try:
            if preset == "Natural RGB":
                img = rgb_composite(cube.data, idx(650), idx(560), idx(480))
                st.image(img, caption="Natural RGB")
            elif preset == "Vegetation false color":
                img = rgb_composite(cube.data, idx(800), idx(670), idx(560))
                st.image(img, caption="Vegetation false color")
            elif preset == "SWIR composite":
                img = rgb_composite(cube.data, idx(2200), idx(1650), idx(900))
                st.image(img, caption="SWIR composite")
            elif preset == "NDVI":
                ndvi = normalized_difference(cube.data[idx(800)], cube.data[idx(670)])
                st.image(stretch_to_uint8(ndvi), caption="NDVI")
            elif preset == "NDWI":
                # Scientific assumption: NDWI uses green and NIR (McFeeters-style) unless a sensor-specific definition is provided.
                ndwi = normalized_difference(cube.data[idx(560)], cube.data[idx(860)])
                st.image(stretch_to_uint8(ndwi), caption="NDWI")
            elif preset == "Red-edge visualization":
                red_edge = cube.data[idx(705)]
                st.image(stretch_to_uint8(red_edge), caption="Red-edge band")
            elif preset == "PCA":
                pca = pca_cube(cube.data, n_components=3)
                img = rgb_composite(pca, 0, 1, 2)
                st.image(img, caption="PCA composite")
        except ValueError as exc:
            st.error(f"Preset cannot be rendered: {exc}")

    with tab_spectrum:
        c1, c2 = st.columns(2)
        row = c1.number_input("Row", min_value=0, max_value=cube.data.shape[1] - 1, value=0)
        col = c2.number_input("Column", min_value=0, max_value=cube.data.shape[2] - 1, value=0)
        try:
            spec = extract_pixel_spectrum(cube.data, int(row), int(col))
            has_finite_wavelengths = len(cube.wavelengths_nm) == len(spec) and any(math.isfinite(v) for v in cube.wavelengths_nm)
            x = cube.wavelengths_nm if has_finite_wavelengths else list(range(len(spec)))
            st.line_chart(pd.DataFrame({"x": x, "reflectance": spec}).set_index("x"))
        except ValueError as exc:
            st.error(str(exc))

    with tab_stats:
        band = st.slider("Band index", min_value=0, max_value=cube.data.shape[0] - 1, value=0)
        st.json(band_stats(cube.data, band))
else:
    st.info("Enter a local path to a raster file or EnMAP product directory.")
