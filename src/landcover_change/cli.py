"""Compare two classified land-cover rasters.

Run: PYTHONPATH=src python -m landcover_change.cli before.tif after.tif
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from landcover_change.change import change_summary, forest_loss_ha, transition_matrix_ha
from landcover_change.raster_io import assert_same_grid, read_classified


def main(argv: list[str] | None = None) -> None:
    """Print a change summary, the transition matrix and gross forest loss."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    args = parser.parse_args(argv)

    a, area, pa = read_classified(args.before)
    b, _, pb = read_classified(args.after)
    assert_same_grid(pa, pb)
    summary = change_summary(a, b, area)
    matrix = transition_matrix_ha(a, b, area)
    args.out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out / "change_summary.csv", encoding="utf-8")
    matrix.to_csv(args.out / "transition_matrix_ha.csv", encoding="utf-8")
    print(summary.round(1).to_string())
    print(f"\nGross forest loss: {forest_loss_ha(a, b, area):,.0f} ha")


if __name__ == "__main__":
    main()
