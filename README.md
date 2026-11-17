# South West Mau Forest: land-cover change 2000–2024

Change detection for the South West Mau Forest, the headwaters of the Nyangores and Amala rivers that form the Mara. My GeoNova analysis found about **10,200 ha of forest loss** and a **172% expansion of tea and cropland** between 2000 and 2024.

## Why it matters

The Mau is Kenya's largest closed-canopy montane forest and a water tower for the Mara basin, Lake Victoria and the Maasai Mara. Forest loss reduces dry-season river flows and raises erosion, which makes downstream farmers, towns and wildlife more exposed to drought. Ecosystem-based adaptation in the basin starts with knowing where and how fast the forest is changing.

## Workflow

1. `scripts/gee_classify_mau.py`: Google Earth Engine script that builds dry-season Landsat composites for 2000 and 2024, classifies them (Random Forest) and exports both maps on the same 30 m grid in EPSG:21036. Requires `earthengine-api` and authentication, so it is not run in CI.
2. `landcover_change`: compares the two maps and reports
   - area per class at both dates, with absolute and percentage change
   - a transition matrix in hectares (what each class became)
   - gross forest loss

Classes: 1 forest · 2 tea and cropland · 3 grassland and shrubland · 4 settlement and bare · 5 water (0 = nodata).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                # run the tests
```

```bash
PYTHONPATH=src python -m landcover_change.cli lc_2000.tif lc_2024.tif --out outputs
```

The tool refuses rasters in a geographic CRS (area would be wrong) and rasters that are not on the same grid.

## Accuracy

Report an accuracy assessment (confusion matrix from independent reference points) with any published figures. Area estimates should be adjusted for classification error (Olofsson et al., 2014) before use in policy.

## Author

Kiplangat Elisha · Climate adaptation and geospatial analyst · [geonova.co.ke](https://www.geonova.co.ke)
