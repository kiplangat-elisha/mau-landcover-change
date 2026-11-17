import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from landcover_change.change import (
    change_summary,
    class_areas_ha,
    forest_loss_ha,
    transition_matrix_ha,
)
from landcover_change.cli import main
from landcover_change.raster_io import assert_same_grid, read_classified

PX = 900.0  # 30 m pixel


def test_areas_exclude_nodata():
    arr = np.array([[1, 1], [2, 0]])
    a = class_areas_ha(arr, PX)
    assert a["forest"] == pytest.approx(0.18)
    assert a["tea and cropland"] == pytest.approx(0.09)
    assert a["water"] == 0


def test_transition_and_loss():
    before = np.array([[1, 1, 1, 1]])
    after = np.array([[1, 2, 2, 0]])
    tm = transition_matrix_ha(before, after, PX)
    assert tm.loc["forest", "tea and cropland"] == pytest.approx(0.18)
    assert forest_loss_ha(before, after, PX) == pytest.approx(0.18)


def test_summary_pct():
    before = np.array([[1, 1, 2, 2]])
    after = np.array([[1, 2, 2, 2]])
    s = change_summary(before, after, PX)
    assert s.loc["tea and cropland", "change_pct"] == pytest.approx(50.0)
    assert np.isnan(s.loc["water", "change_pct"])


def test_shape_mismatch():
    with pytest.raises(ValueError):
        transition_matrix_ha(np.ones((2, 2)), np.ones((3, 3)), PX)


def test_bad_pixel_area():
    with pytest.raises(ValueError):
        class_areas_ha(np.ones((2, 2), dtype=int), 0)


def _write(path, arr, crs="EPSG:21036"):
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1],
                       count=1, dtype="uint8", crs=crs, transform=from_origin(0, 0, 30, 30),
                       nodata=0) as dst:
        dst.write(arr.astype("uint8"), 1)


def test_io_and_cli(tmp_path, capsys):
    b, a = tmp_path / "b.tif", tmp_path / "a.tif"
    _write(b, np.array([[1, 1], [1, 3]]))
    _write(a, np.array([[1, 2], [2, 3]]))
    arr, area, prof = read_classified(b)
    assert area == pytest.approx(900)
    assert_same_grid(prof, read_classified(a)[2])
    main([str(b), str(a), "--out", str(tmp_path / "out")])
    assert "Gross forest loss" in capsys.readouterr().out
    assert (tmp_path / "out" / "transition_matrix_ha.csv").exists()


def test_geographic_raster_rejected(tmp_path):
    p = tmp_path / "g.tif"
    _write(p, np.ones((2, 2)), crs="EPSG:4326")
    with pytest.raises(ValueError):
        read_classified(p)
