"""
Correction framework.

This starter tool intentionally does not apply generic radiometric,
atmospheric, or geometric corrections without sensor/product metadata.
"""

def radiometric_requirements():
    return {
        "purpose": "Convert raw digital numbers into calibrated radiance or reflectance.",
        "required_inputs": [
            "Sensor/product identification",
            "Product processing level",
            "Gain and offset/calibration coefficients",
            "Acquisition metadata",
            "Solar geometry when applicable",
        ],
        "status": "Framework ready; sensor-specific adapter required.",
    }

def atmospheric_requirements():
    return {
        "purpose": "Estimate surface reflectance by reducing atmospheric effects.",
        "required_inputs": [
            "Radiometrically calibrated data",
            "Acquisition time",
            "Solar and viewing geometry",
            "Atmospheric model",
            "Aerosol/water-vapor information where required",
            "Sensor spectral response information",
        ],
        "status": "Framework ready; use a validated sensor/product workflow.",
    }

def geometric_requirements():
    return {
        "purpose": "Georeference, orthorectify, or co-register imagery.",
        "required_inputs": [
            "Sensor geometry",
            "Existing georeferencing metadata",
            "CRS",
            "DEM when orthorectification is required",
            "Ground/control information where necessary",
        ],
        "status": "Framework ready; correction depends on the input product.",
    }
