"""
Environment Verification Script for Member 2 (GIS / Remote Sensing Engineer).
Tests imports and configuration for:
numpy, pandas, rasterio, geopandas, shapely, pyproj, fiona, matplotlib, scipy, rioxarray, xarray
"""

import sys

def verify_gis_stack():
    print("=" * 65)
    print("VIT_MAPATHON - Member 2 (GIS / Remote Sensing) Environment Check")
    print("=" * 65)
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version   : {sys.version.split()[0]}")
    print("-" * 65)

    packages = [
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("rasterio", "rasterio"),
        ("geopandas", "geopandas"),
        ("shapely", "shapely"),
        ("pyproj", "pyproj"),
        ("fiona", "fiona"),
        ("matplotlib", "matplotlib"),
        ("scipy", "scipy"),
        ("rioxarray", "rioxarray"),
        ("xarray", "xarray"),
    ]

    all_passed = True

    for name, module_name in packages:
        try:
            mod = __import__(module_name)
            ver = getattr(mod, "__version__", "unknown")
            print(f"  [OK] {name:<15} : v{ver}")
        except Exception as e:
            print(f"  [FAIL] {name:<15} : Error ({e})")
            all_passed = False

    print("-" * 65)
    if all_passed:
        import rasterio
        import pyproj
        print(f"Rasterio GDAL Version: {rasterio.__gdal_version__}")
        print(f"PyProj PROJ Version   : {pyproj.__proj_version__}")
        print("=" * 65)
        print("ALL GIS DEPENDENCIES SUCCESSFULLY VERIFIED!")
        print("=" * 65)
        return 0
    else:
        print("=" * 65)
        print("SOME DEPENDENCIES FAILED TO IMPORT.")
        print("=" * 65)
        return 1

if __name__ == "__main__":
    sys.exit(verify_gis_stack())
