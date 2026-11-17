"""Read classified GeoTIFFs and check they share a grid before comparing them."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio


def read_classified(path: Path) -> tuple[np.ndarray, float, rasterio.profiles.Profile]:
    """Read band 1 of a classified raster and return (array, pixel area m², profile).

    Raises:
        ValueError: If the raster is not in a projected CRS (pixel area undefined).
    """
    with rasterio.open(Path(path)) as src:
        if src.crs is None or not src.crs.is_projected:
            raise ValueError(f"{path} must be in a projected CRS to measure area.")
        arr = src.read(1)
        pixel_area = abs(src.transform.a * src.transform.e)
        return arr, pixel_area, src.profile


def assert_same_grid(profile_a: dict, profile_b: dict) -> None:
    """Raise ValueError unless both rasters share CRS, transform and size."""
    for key in ("crs", "transform", "width", "height"):
        if profile_a[key] != profile_b[key]:
            raise ValueError(f"Rasters differ in {key}; resample to a common grid first.")
