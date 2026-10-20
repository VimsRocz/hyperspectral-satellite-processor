from __future__ import annotations

from pathlib import Path
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from satproc.io import (
    directory_signature,
    discover_rasters,
    file_signature,
    get_band_labels,
    get_wavelengths,
    inspect_raster,
    save_uploaded_files,
)
from satproc.metadata import find_nearest_band
from satproc.processing import (
    calculate_stats,
    normalized_difference,
    pca_rgb,
    percentile_stretch,
    read_band_preview,
    read_rgb_files,
    read_rgb_preview,
    spectral_profile,
)
from satproc.corrections import (
    atmospheric_requirements,
    geometric_requirements,
    radiometric_requirements,
)
from satproc.sensors import get_sensor_info

st.set_page_config(
    page_title="Hyperspectral Satellite Processor",
    page_icon="🛰️",
    layout="wide",
)

# ------------------------------- cache layer -------------------------------

@st.cache_data(show_spinner=False)
def cached_discover(root: str, signature):
    del signature
    return [str(p) for p in discover_rasters(root)]

@st.cache_data(show_spinner=False)
def cached_inspect(path: str, signature):
    del signature
    return inspect_raster(path)

@st.cache_data(show_spinner=False)
def cached_labels(path: str, signature):
    del signature
    return get_band_labels(path)

@st.cache_data(show_spinner=False)
def cached_wavelengths(path: str, signature):
    del signature
    return get_wavelengths(path)

@st.cache_data(show_spinner=False)
def cached_band_preview(path: str, band: int, max_dim: int, signature):
    del signature
    return read_band_preview(path, band=band, max_dim=max_dim)

@st.cache_data(show_spinner=False)
def cached_rgb(path: str, r: int, g: int, b: int, low: int, high: int, max_dim: int, signature):
    del signature
    return read_rgb_preview(path, r, g, b, low, high, max_dim)

@st.cache_data(show_spinner=False)
def cached_stats(path: str, band: int, signature):
    del signature
    return calculate_stats(path, band)

@st.cache_data(show_spinner=False)
def cached_index(path: str, a: int, b: int, max_dim: int, signature):
    del signature
    return normalized_difference(path, a, b, max_dim)

@st.cache_data(show_spinner=False)
def cached_pca(path: str, max_dim: int, max_fit_pixels: int, signature):
    del signature
    return pca_rgb(path, max_dim=max_dim, max_fit_pixels=max_fit_pixels)

# ------------------------------- helpers ----------------------------------

def display_name(path: str, root: Path) -> str:
    try:
        return str(Path(path).relative_to(root))
    except Exception:
        return Path(path).name

def role_message(role: str):
    if role == "quality_mask":
        st.warning("You selected a quality/mask layer. Select a SPECTRAL_IMAGE file for main spectral analysis.")
    elif role == "quicklook":
        st.warning("You selected a quicklook image. Use the science raster for full spectral analysis.")
    elif role == "science_image":
        st.success("Science image detected.")

def next_step(info: dict):
    sensor = info["sensor_guess"]
    level = info["product_level"]
    role = info["file_role"]
    if role != "science_image" and sensor == "EnMAP":
        return "Select SPECTRAL_IMAGE.BSQ (or VNIR/SWIR science cube) before spectral analysis."
    if sensor == "EnMAP" and level == "L1B":
        return "For surface-reflectance analysis, prefer EnMAP L2A. L1B is useful for radiance-oriented workflows."
    if sensor == "EnMAP" and level == "L2A":
        return "Try Natural RGB → Spectral Profile → NDVI → PCA."
    if sensor == "Sentinel-2":
        return "For most terrestrial workflows, use Level-2A and verify band resolution/alignment."
    if sensor == "Landsat":
        return "Prefer Collection 2 Level-2 for many surface analyses; keep thermal and reflectance bands conceptually separate."
    return "Inspect metadata first, then verify data quantity before scientific interpretation."

# ------------------------------- header -----------------------------------

st.title("🛰️ Hyperspectral Satellite Processor")
st.caption(
    "Local, sensor-aware exploratory processing for hyperspectral and multispectral Earth-observation imagery."
)

st.sidebar.header("Dataset")
source_mode = st.sidebar.radio("Data source", ["Local folder/path", "Upload files"])
dataset_root = None

if source_mode == "Upload files":
    st.sidebar.info("For large hyperspectral products, Local folder/path is faster and avoids browser upload overhead.")
    uploaded_files = st.sidebar.file_uploader(
        "Upload product files",
        type=["tif", "tiff", "jp2", "img", "dat", "hdr", "bsq", "bil", "bip", "xml", "zip"],
        accept_multiple_files=True,
    )
    if st.sidebar.button("Load uploaded dataset", type="primary") and uploaded_files:
        old = st.session_state.get("uploaded_dataset_root")
        if old and Path(old).exists():
            st.session_state.pop("uploaded_dataset_root", None)
        temp_dir = Path(tempfile.mkdtemp(prefix="satellite_processor_"))
        try:
            save_uploaded_files(uploaded_files, temp_dir)
        except Exception as exc:
            st.sidebar.error(f"Upload/extraction failed: {exc}")
        else:
            st.session_state["uploaded_dataset_root"] = str(temp_dir)
    if "uploaded_dataset_root" in st.session_state:
        dataset_root = Path(st.session_state["uploaded_dataset_root"])
else:
    local_path = st.sidebar.text_input(
        "Local file or folder",
        placeholder="/Users/you/Downloads/ENMAP01-____L2A-...",
    )
    if local_path:
        dataset_root = Path(local_path).expanduser()

if dataset_root is None:
    st.info("Choose a local dataset folder or upload supported files.")
    st.stop()

if not dataset_root.exists():
    st.error("The selected local path does not exist.")
    st.stop()

dir_sig = directory_signature(dataset_root)
rasters = cached_discover(str(dataset_root.resolve()), dir_sig)
if not rasters:
    st.error("No readable GeoTIFF/JP2/ENVI raster was found.")
    st.stop()

selected_path = st.sidebar.selectbox(
    "Raster",
    rasters,
    format_func=lambda p: display_name(p, dataset_root),
)
sig = file_signature(selected_path)

try:
    info, tags = cached_inspect(selected_path, sig)
    band_labels = cached_labels(selected_path, sig)
    wavelengths = cached_wavelengths(selected_path, sig)
except Exception as exc:
    st.error(f"Could not inspect raster: {exc}")
    st.stop()

band_count = int(info["bands"])
width = int(info["width"])
height = int(info["height"])

role_message(info["file_role"])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Sensor", info["sensor_guess"])
c2.metric("Product", info["product_level"])
c3.metric("Bands", band_count)
c4.metric("Width", width)
c5.metric("Height", height)

st.info(f"**Recommended next step:** {next_step(info)}")

tabs = st.tabs([
    "Dataset Inspector",
    "Sensor & Product",
    "Band Viewer",
    "RGB / False Color",
    "Spectrum",
    "PCA",
    "Spectral Indices",
    "Processing Pipeline",
])

# --------------------------- dataset inspector -----------------------------

with tabs[0]:
    st.subheader("Dataset information")
    table = pd.DataFrame({"Property": list(info.keys()), "Value": list(info.values())})
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("Spectral metadata")
    if wavelengths:
        st.success(f"Wavelength metadata detected for {len(wavelengths)} bands.")
        st.dataframe(
            pd.DataFrame({"Band": range(1, len(wavelengths) + 1), "Wavelength (nm)": wavelengths}),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No complete wavelength vector was detected in this raster metadata.")

    with st.expander("Raw dataset tags"):
        st.json(tags)

# ---------------------------- sensor product -------------------------------

with tabs[1]:
    st.subheader("Sensor & Product")
    sensor = get_sensor_info(info["sensor_guess"])
    if sensor:
        left, right = st.columns([2, 1])
        with left:
            st.markdown(f"### {sensor.name}")
            st.write(sensor.mission)
            product_table = pd.DataFrame(
                {
                    "Field": [
                        "Sensor type",
                        "Detected product",
                        "Selected file role",
                        "Data quantity",
                        "Recommended product",
                        "Supported levels",
                    ],
                    "Value": [
                        sensor.type,
                        info["product_level"],
                        info["file_role"],
                        info["data_quantity"],
                        sensor.recommended_product,
                        ", ".join(sensor.supported_levels),
                    ],
                }
            )
            st.dataframe(product_table, use_container_width=True, hide_index=True)
            st.write(sensor.notes)
        with right:
            st.link_button("Official mission", sensor.official_url, use_container_width=True)
            st.link_button("Official data access", sensor.data_url, use_container_width=True)
            st.link_button("Documentation / examples", sensor.documentation_url, use_container_width=True)
    else:
        st.info("Generic raster detected. Sensor-specific scientific assumptions are not available.")

    if info["sensor_guess"] == "EnMAP":
        if info["product_level"] == "L1B":
            st.warning("EnMAP L1B is not surface reflectance. Do not interpret stored values as L2A reflectance.")
        elif info["product_level"] == "L2A":
            st.success("EnMAP L2A is the preferred level in this tool for surface-reflectance spectral analysis.")

# ------------------------------ band viewer --------------------------------

with tabs[2]:
    st.subheader("Single-band visualization")
    band = st.selectbox(
        "Band",
        range(1, band_count + 1),
        format_func=lambda x: (
            f"{x}: {band_labels[x - 1]}"
            + (f" — {wavelengths[x - 1]:.2f} nm" if wavelengths and x <= len(wavelengths) else "")
        ),
        key="viewer_band",
    )
    low, high = st.slider("Display percentile stretch", 0, 100, (2, 98))
    image = cached_band_preview(selected_path, band, 900, sig)
    st.image(percentile_stretch(image, low, high), caption=f"Band {band}", clamp=True, use_container_width=True)

    if st.button("Calculate band statistics"):
        st.session_state["stats_result"] = cached_stats(selected_path, band, sig)
    if "stats_result" in st.session_state:
        stats = st.session_state["stats_result"]
        st.dataframe(pd.DataFrame({"Statistic": stats.keys(), "Value": stats.values()}), hide_index=True)

# ------------------------------- RGB ---------------------------------------

with tabs[3]:
    st.subheader("RGB and false-color composites")
    if band_count >= 3:
        preset = st.selectbox("Preset", ["Manual", "Natural Color", "Vegetation False Color", "SWIR False Color"])
        if preset != "Manual" and wavelengths:
            targets = {
                "Natural Color": (665.0, 560.0, 490.0),
                "Vegetation False Color": (842.0, 665.0, 560.0),
                "SWIR False Color": (1650.0, 842.0, 665.0),
            }[preset]
            try:
                rb, rw = find_nearest_band(wavelengths, targets[0])
                gb, gw = find_nearest_band(wavelengths, targets[1])
                bb, bw = find_nearest_band(wavelengths, targets[2])
                st.caption(f"Selected wavelengths: R {rw:.1f} nm (B{rb}), G {gw:.1f} nm (B{gb}), B {bw:.1f} nm (B{bb})")
            except Exception as exc:
                st.warning(str(exc))
                rb, gb, bb = 1, min(2, band_count), min(3, band_count)
        else:
            if preset != "Manual" and not wavelengths:
                st.info("Preset selection needs wavelength metadata; using manual mode.")
            rb = st.selectbox("Red channel", range(1, band_count + 1), key="rgb_r")
            gb = st.selectbox("Green channel", range(1, band_count + 1), key="rgb_g")
            bb = st.selectbox("Blue channel", range(1, band_count + 1), key="rgb_b")

        rgb_low, rgb_high = st.slider("RGB percentile stretch", 0, 100, (2, 98), key="rgb_stretch")
        if st.button("Create composite"):
            st.session_state["rgb_result"] = cached_rgb(selected_path, rb, gb, bb, rgb_low, rgb_high, 900, sig)
            st.session_state["rgb_caption"] = f"{preset}: bands {rb}/{gb}/{bb}"
        if "rgb_result" in st.session_state:
            st.image(st.session_state["rgb_result"], caption=st.session_state.get("rgb_caption", "RGB"), use_container_width=True)
    else:
        st.info("This selected raster has fewer than three bands.")

# ----------------------------- spectrum ------------------------------------

with tabs[4]:
    st.subheader("Spectral profile")
    if band_count < 2:
        st.info("A multiband raster is required.")
    else:
        a, b, c = st.columns(3)
        row = a.number_input("Pixel row", 0, height - 1, min(height // 2, height - 1))
        col = b.number_input("Pixel column", 0, width - 1, min(width // 2, width - 1))
        radius = c.number_input("ROI radius (pixels)", 0, 20, 0)

        if st.button("Read spectrum"):
            values = spectral_profile(selected_path, int(row), int(col), int(radius))
            x = wavelengths if wavelengths and len(wavelengths) == len(values) else list(range(1, len(values) + 1))
            st.session_state["spectrum_result"] = (x, values)
        if "spectrum_result" in st.session_state:
            x, values = st.session_state["spectrum_result"]
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(x, values)
            ax.set_xlabel("Wavelength (nm)" if wavelengths else "Band")
            ax.set_ylabel(info["data_quantity"] if info["data_quantity"] != "Unknown / sensor-dependent" else "Pixel value")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close(fig)
            csv = pd.DataFrame({"wavelength_or_band": x, "value": values}).to_csv(index=False).encode()
            st.download_button("Download spectrum CSV", csv, "spectrum.csv", "text/csv")

# -------------------------------- PCA --------------------------------------

with tabs[5]:
    st.subheader("PCA visualization")
    max_dim = st.slider("PCA preview dimension", 120, 320, 220, step=20)
    max_fit = st.select_slider("Maximum PCA fit pixels", options=[5000, 10000, 20000, 50000], value=20000)
    if st.button("Run PCA"):
        with st.spinner("Running sampled PCA..."):
            st.session_state["pca_result"] = cached_pca(selected_path, max_dim, max_fit, sig)
    if "pca_result" in st.session_state:
        pca_image, variance = st.session_state["pca_result"]
        st.image(pca_image, caption="PCA components 1–3", use_container_width=True)
        st.dataframe(
            pd.DataFrame({"Component": ["PC1", "PC2", "PC3"], "Explained variance": variance}),
            hide_index=True,
        )

# --------------------------- spectral indices ------------------------------

with tabs[6]:
    st.subheader("Spectral indices")
    if band_count < 2:
        st.info("At least two bands are required.")
    else:
        index_name = st.selectbox("Index", ["Manual normalized difference", "NDVI", "NDWI", "NDMI", "Red-edge NDVI"])
        pair = None
        if index_name != "Manual normalized difference":
            if not wavelengths:
                st.warning("Automatic index presets require wavelength metadata.")
            else:
                targets = {
                    "NDVI": (842.0, 665.0),
                    "NDWI": (560.0, 842.0),
                    "NDMI": (842.0, 1650.0),
                    "Red-edge NDVI": (750.0, 705.0),
                }[index_name]
                a_band, a_nm = find_nearest_band(wavelengths, targets[0])
                b_band, b_nm = find_nearest_band(wavelengths, targets[1])
                pair = (a_band, b_band)
                st.caption(f"A: B{a_band} ({a_nm:.1f} nm) · B: B{b_band} ({b_nm:.1f} nm)")
        else:
            pair = (
                st.selectbox("Band A", range(1, band_count + 1), key="idx_a"),
                st.selectbox("Band B", range(1, band_count + 1), key="idx_b"),
            )

        if pair and st.button("Calculate index"):
            st.session_state["index_result"] = cached_index(selected_path, pair[0], pair[1], 900, sig)
            st.session_state["index_name"] = index_name
        if "index_result" in st.session_state:
            arr = st.session_state["index_result"]
            fig, ax = plt.subplots(figsize=(10, 6))
            im = ax.imshow(arr, vmin=-1, vmax=1)
            ax.set_title(st.session_state.get("index_name", "Normalized Difference"))
            ax.axis("off")
            fig.colorbar(im, ax=ax, label="Index")
            st.pyplot(fig)
            plt.close(fig)

# -------------------------- processing pipeline ----------------------------

with tabs[7]:
    st.subheader("Scientific processing status")
    st.write(
        "The application performs exploratory reading, visualization, PCA and indices. "
        "It does not silently apply mission-specific radiometric, atmospheric or geometric corrections."
    )
    st.markdown("### Radiometric correction requirements")
    st.json(radiometric_requirements())
    st.markdown("### Atmospheric correction requirements")
    st.json(atmospheric_requirements())
    st.markdown("### Geometric correction requirements")
    st.json(geometric_requirements())
    st.markdown(
        """
### Architecture

Satellite product → sensor/product identification → cached metadata →
cached previews → wavelength-aware visualization → spectrum / PCA / indices.

Sensor-specific adapters keep mission knowledge separate from the generic processing engine.
"""
    )
