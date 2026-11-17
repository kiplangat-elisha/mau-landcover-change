"""Area statistics and transition (change) matrix between two classified rasters."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd

from landcover_change import CLASSES, NODATA

M2_PER_HA = 10_000.0
FOREST_CLASS = 1


def class_areas_ha(classified: npt.NDArray[np.integer], pixel_area_m2: float) -> pd.Series:
    """Area in hectares of each class, excluding nodata.

    Args:
        classified: 2-D array of class codes.
        pixel_area_m2: Area of one pixel in m² (e.g. 900 for 30 m Landsat).

    Returns:
        Series indexed by class name, including classes with zero area.
    """
    if pixel_area_m2 <= 0:
        raise ValueError("pixel_area_m2 must be positive.")
    codes, counts = np.unique(classified[classified != NODATA], return_counts=True)
    found = dict(zip(codes.tolist(), counts.tolist(), strict=True))
    return pd.Series(
        {name: found.get(code, 0) * pixel_area_m2 / M2_PER_HA for code, name in CLASSES.items()},
        name="area_ha",
    )


def transition_matrix_ha(
    before: npt.NDArray[np.integer], after: npt.NDArray[np.integer], pixel_area_m2: float
) -> pd.DataFrame:
    """Cross-tabulate classes between two dates, in hectares.

    Rows are the earlier class and columns the later class. Pixels that are nodata
    in either date are excluded, so both maps must be co-registered on the same grid.

    Raises:
        ValueError: If the arrays have different shapes.
    """
    if before.shape != after.shape:
        raise ValueError("before and after must have the same shape (same grid).")
    valid = (before != NODATA) & (after != NODATA)
    codes = list(CLASSES)
    n = len(codes)
    index = {c: i for i, c in enumerate(codes)}
    mat = np.zeros((n, n), dtype=np.int64)
    b = before[valid].ravel()
    a = after[valid].ravel()
    known = np.isin(b, codes) & np.isin(a, codes)
    np.add.at(mat, (np.vectorize(index.get)(b[known]), np.vectorize(index.get)(a[known])), 1)
    names = [CLASSES[c] for c in codes]
    return pd.DataFrame(mat * pixel_area_m2 / M2_PER_HA, index=names, columns=names)


def change_summary(
    before: npt.NDArray[np.integer], after: npt.NDArray[np.integer], pixel_area_m2: float
) -> pd.DataFrame:
    """Area per class at both dates with absolute and percentage change."""
    df = pd.DataFrame(
        {
            "before_ha": class_areas_ha(before, pixel_area_m2),
            "after_ha": class_areas_ha(after, pixel_area_m2),
        }
    )
    df["change_ha"] = df["after_ha"] - df["before_ha"]
    df["change_pct"] = (df["change_ha"] / df["before_ha"].where(df["before_ha"] > 0)) * 100
    return df


def forest_loss_ha(
    before: npt.NDArray[np.integer], after: npt.NDArray[np.integer], pixel_area_m2: float
) -> float:
    """Gross forest loss: area that was forest before and is any other class after."""
    tm = transition_matrix_ha(before, after, pixel_area_m2)
    forest = CLASSES[FOREST_CLASS]
    return float(tm.loc[forest].sum() - tm.loc[forest, forest])
