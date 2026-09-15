\
from pathlib import Path
import tempfile

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import rasterio

from satproc.io import (
    save_uploaded_files,
    discover_rasters,
    inspect_raster,
    get_wavelengths,
    get_band_labels,
)
from satproc.processing import (
    read_band_preview,
    read_rgb_preview,
    read_rgb_files,
    calculate_stats,
    percentile_stretch,
    spectral_profile,
    pca_rgb,
    normalized_difference,
)
from satproc.corrections import (
    radiometric_requirements,
    atmospheric_requirements,
    geometric_requirements,
)

st.set_page_config(
    page_title="Satellite & Hyperspectral Processor",
    page_icon="🛰️",
    layout="wide",
)

st.title("🛰️ Satellite & Hyperspectral Image Processor")
st.caption(
    "Local web application for inspecting and exploring multispectral "
    "and hyperspectral Earth-observation imagery."
)

st.sidebar.header("1. Dataset")
source_mode = st.sidebar.radio(
    "Data source", ["Upload files", "Local folder/path"]
)
dataset_root = None

if source_mode == "Upload files":
    uploaded_files = st.sidebar.file_uploader(
        "Upload raster/product files",
        type=["tif", "tiff", "jp2", "img", "dat", "hdr", "bsq", "bil", "bip", "xml", "zip"],
        accept_multiple_files=True,
    )
    if st.sidebar.button("Load uploaded dataset", type="primary"):
        if uploaded_files:
            temp_dir = Path(tempfile.mkdtemp(prefix="satellite_processor_"))
            save_uploaded_files(uploaded_files, temp_dir)
            st.session_state["uploaded_dataset_root"] = str(temp_dir)

    if "uploaded_dataset_root" in st.session_state:
        dataset_root = Path(st.session_state["uploaded_dataset_root"])
else:
    local_path = st.sidebar.text_input(
        "Local file or folder", placeholder=r"C:\data\EnMAP"
    )
    if local_path:
        dataset_root = Path(local_path).expanduser()

if dataset_root is None:
    st.info("Upload imagery or enter the path to a local satellite dataset.")
    st.stop()

rasters = discover_rasters(dataset_root)
if not rasters:
    st.error(
        "No readable raster files were found. Supported examples include "
        "GeoTIFF, JP2 and ENVI rasters."
    )
    st.stop()

def display_name(path):
    try:
        return str(path.relative_to(dataset_root))
    except Exception:
        return path.name

selected_path = st.sidebar.selectbox(
    "Raster", rasters, format_func=display_name
)

try:
    info, tags = inspect_raster(selected_path)
except Exception as exc:
    st.error(f"Could not open raster: {exc}")
    st.stop()

with rasterio.open(selected_path) as src:
    band_count = src.count
    width = src.width
    height = src.height

band_labels = get_band_labels(selected_path)
wavelengths = get_wavelengths(selected_path)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Bands", info["bands"])
col2.metric("Width", info["width"])
col3.metric("Height", info["height"])
col4.metric("Sensor", info["sensor_guess"])
st.write("**Estimated image type:**", info["image_type_guess"])

tabs = st.tabs(
    [
        "Dataset Inspector",
        "Band Viewer",
        "RGB / False Color",
        "Spectrum & PCA",
        "Spectral Index",
        "Processing Pipeline",
    ]
)

with tabs[0]:
    st.subheader("Dataset information")
    table = pd.DataFrame(
        {"Property": list(info.keys()), "Value": list(info.values())}
    )
    st.dataframe(table, use_container_width=True, hide_index=True)

    if wavelengths:
        st.success(
            f"Wavelength metadata detected for {len(wavelengths)} bands."
        )
        wavelength_table = pd.DataFrame(
            {"Band": range(1, len(wavelengths) + 1), "Wavelength": wavelengths}
        )
        st.dataframe(
            wavelength_table, use_container_width=True, hide_index=True
        )
    else:
        st.info(
            "No complete wavelength vector was detected inside this raster metadata."
        )

    with st.expander("Raw raster metadata"):
        st.json(tags)

with tabs[1]:
    st.subheader("Single-band visualization")
    band = st.selectbox(
        "Band",
        range(1, band_count + 1),
        format_func=lambda x: f"{x}: {band_labels[x - 1]}",
        key="viewer_band",
    )
    low, high = st.slider(
        "Display percentile stretch", 0, 100, (2, 98)
    )
    try:
        image = read_band_preview(selected_path, band=band)
        displayed = percentile_stretch(image, low, high)
        st.image(
            displayed,
            caption=f"Band {band}",
            clamp=True,
            use_container_width=True,
        )
    except Exception as exc:
        st.error(str(exc))

    if st.button("Calculate band statistics"):
        statistics = calculate_stats(selected_path, band)
        if statistics:
            stat_table = pd.DataFrame(
                {
                    "Statistic": list(statistics.keys()),
                    "Value": list(statistics.values()),
                }
            )
            st.dataframe(
                stat_table, hide_index=True, use_container_width=True
            )

with tabs[2]:
    st.subheader("RGB and false-color composite")
    rgb_mode = st.radio(
        "Composite source",
        ["Bands inside current raster", "Three separate raster files"],
    )
    rgb_low, rgb_high = st.slider(
        "RGB percentile stretch", 0, 100, (2, 98), key="rgb_stretch"
    )

    if rgb_mode == "Bands inside current raster":
        if band_count < 3:
            st.warning(
                "This raster contains fewer than three bands. Use the "
                "separate-raster option for datasets such as Sentinel-2 band files."
            )
        else:
            r = st.selectbox(
                "Red channel",
                range(1, band_count + 1),
                index=min(2, band_count - 1),
                key="r_band",
            )
            g = st.selectbox(
                "Green channel",
                range(1, band_count + 1),
                index=min(1, band_count - 1),
                key="g_band",
            )
            b = st.selectbox(
                "Blue channel", range(1, band_count + 1), index=0, key="b_band"
            )
            if st.button("Create composite", key="same_raster_rgb"):
                try:
                    rgb = read_rgb_preview(
                        selected_path, r, g, b, rgb_low, rgb_high
                    )
                    st.image(
                        rgb,
                        caption=f"RGB = {r}/{g}/{b}",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(str(exc))
    else:
        if len(rasters) < 3:
            st.warning("At least three readable raster files are required.")
        else:
            red_file = st.selectbox(
                "Red channel file",
                rasters,
                format_func=display_name,
                key="red_file",
            )
            green_file = st.selectbox(
                "Green channel file",
                rasters,
                format_func=display_name,
                key="green_file",
            )
            blue_file = st.selectbox(
                "Blue channel file",
                rasters,
                format_func=display_name,
                key="blue_file",
            )
            if st.button("Create multi-file composite"):
                try:
                    rgb = read_rgb_files(
                        red_file,
                        green_file,
                        blue_file,
                        rgb_low,
                        rgb_high,
                    )
                    st.image(
                        rgb,
                        caption="Multi-file RGB / false-color composite",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(str(exc))

with tabs[3]:
    st.subheader("Spectral analysis")
    if band_count < 2:
        st.info(
            "Spectral profiles require a multiband raster. A single "
            "Sentinel/Landsat band cannot produce a spectrum by itself."
        )
    else:
        col_row, col_column = st.columns(2)
        row = col_row.number_input(
            "Pixel row",
            min_value=0,
            max_value=height - 1,
            value=min(height // 2, height - 1),
        )
        column = col_column.number_input(
            "Pixel column",
            min_value=0,
            max_value=width - 1,
            value=min(width // 2, width - 1),
        )
        if st.button("Read pixel spectrum"):
            try:
                spectrum = spectral_profile(
                    selected_path, int(row), int(column)
                )
                if wavelengths and len(wavelengths) == len(spectrum):
                    x = wavelengths
                    xlabel = "Wavelength"
                else:
                    x = list(range(1, len(spectrum) + 1))
                    xlabel = "Band"

                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(x, spectrum, marker=".")
                ax.set_xlabel(xlabel)
                ax.set_ylabel("Pixel value")
                ax.set_title(f"Spectrum at row {row}, column {column}")
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close(fig)
            except Exception as exc:
                st.error(str(exc))

        st.divider()
        st.subheader("PCA visualization")
        st.write(
            "The first three principal components are mapped to RGB. "
            "Useful for exploratory hyperspectral visualization."
        )
        if st.button("Run PCA"):
            with st.spinner("Calculating PCA preview..."):
                try:
                    pca_image, variance = pca_rgb(selected_path)
                    st.image(
                        pca_image,
                        caption="PCA components 1–3",
                        use_container_width=True,
                    )
                    variance_table = pd.DataFrame(
                        {
                            "Component": ["PC1", "PC2", "PC3"],
                            "Explained variance": variance,
                        }
                    )
                    st.dataframe(
                        variance_table,
                        hide_index=True,
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(str(exc))

with tabs[4]:
    st.subheader("Normalized Difference Index")
    st.latex(r"ND = \frac{A-B}{A+B}")
    st.write(
        "For NDVI, select the NIR band as A and the red band as B."
    )

    if band_count < 2:
        st.warning("The current file contains only one band.")
    else:
        index_a = st.selectbox(
            "Band A", range(1, band_count + 1), key="index_a"
        )
        index_b = st.selectbox(
            "Band B", range(1, band_count + 1), key="index_b"
        )
        if st.button("Calculate index"):
            try:
                index_image = normalized_difference(
                    selected_path, index_a, index_b
                )
                fig, ax = plt.subplots(figsize=(10, 6))
                im = ax.imshow(index_image, vmin=-1, vmax=1)
                ax.set_title(
                    f"Normalized Difference ({index_a}, {index_b})"
                )
                ax.axis("off")
                fig.colorbar(im, ax=ax, label="Index")
                st.pyplot(fig)
                plt.close(fig)
            except Exception as exc:
                st.error(str(exc))

with tabs[5]:
    st.subheader("Post-processing architecture")
    st.write(
        "This application separates inspection/visualization from "
        "scientifically sensitive corrections."
    )
    st.markdown("### 1. Radiometric calibration")
    st.json(radiometric_requirements())
    st.markdown("### 2. Atmospheric correction")
    st.json(atmospheric_requirements())
    st.markdown("### 3. Geometric correction")
    st.json(geometric_requirements())
    st.markdown(
        """
### Intended full pipeline

**Raw satellite product**

→ Product identification  
→ Metadata extraction  
→ Radiometric calibration  
→ Geometric / orthorectification check  → Atmospheric correction  
→ Quality masking  
→ Band alignment  
→ Spectral processing  
→ Feature extraction  
→ Classification / target detection  
→ GIS-compatible output
"""
    )
