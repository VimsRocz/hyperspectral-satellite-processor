from satproc.metadata import classify_file_role, detect_product_level, find_nearest_band, quantity_for

def test_file_roles():
    assert classify_file_role("ENMAP-SPECTRAL_IMAGE.BSQ") == "science_image"
    assert classify_file_role("ENMAP-QL_PIXELMASK.TIF") == "quality_mask"
    assert classify_file_role("ENMAP-QL_QUALITY_CLOUD.TIF") == "quality_mask"
    assert classify_file_role("ENMAP-QL_VNIR.TIF") == "quicklook"

def test_product_levels():
    assert detect_product_level("ENMAP01-____L2A-example") == "L2A"
    assert detect_product_level("S2A_MSIL2A_example") == "L2A"
    assert detect_product_level("ENMAP01-____L1B-example") == "L1B"

def test_nearest_band():
    band, wavelength = find_nearest_band([450.0, 560.0, 665.0, 842.0], 670.0)
    assert band == 3
    assert wavelength == 665.0

def test_quantity():
    assert quantity_for("EnMAP", "L2A") == "Surface reflectance"
