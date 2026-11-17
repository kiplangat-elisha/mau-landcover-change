"""Google Earth Engine workflow to produce the classified rasters (not run in CI).

Requires: pip install earthengine-api==1.* and `earthengine authenticate`.
It builds dry-season Landsat median composites for 2000 and 2024 over the
South West Mau, classifies them with a Random Forest trained on your reference
points, and exports both maps on the same 30 m grid (EPSG:21036) to Drive.
Use the exported GeoTIFFs with ``landcover_change.cli``.
"""

from __future__ import annotations

import ee

AOI_BBOX = [35.35, -0.85, 35.85, -0.35]  # approximate South West Mau extent (lon/lat)
EXPORT_CRS = "EPSG:21036"
SCALE_M = 30
DRY_SEASON = ("-01-01", "-03-31")
BANDS = ["blue", "green", "red", "nir", "swir1", "swir2"]


def _mask_and_scale(img: ee.Image) -> ee.Image:
    qa = img.select("QA_PIXEL")
    clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    return img.select("SR_B.*").multiply(0.0000275).add(-0.2).updateMask(clear)


def composite(year: int, aoi: ee.Geometry) -> ee.Image:
    """Dry-season median surface-reflectance composite for one year."""
    if year < 2013:
        col = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        src = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"]
    else:
        col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        src = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
    img = (
        col.filterBounds(aoi)
        .filterDate(f"{year}{DRY_SEASON[0]}", f"{year}{DRY_SEASON[1]}")
        .map(_mask_and_scale)
        .median()
        .select(src, BANDS)
    )
    ndvi = img.normalizedDifference(["nir", "red"]).rename("ndvi")
    return img.addBands(ndvi).clip(aoi)


def classify(year: int, training: ee.FeatureCollection, aoi: ee.Geometry) -> ee.Image:
    """Random Forest classification; ``training`` needs a 'class' property (codes 1–5)."""
    img = composite(year, aoi)
    samples = img.sampleRegions(collection=training, properties=["class"], scale=SCALE_M)
    model = ee.Classifier.smileRandomForest(200).train(samples, "class", img.bandNames())
    return img.classify(model).toByte()


def main(training_asset: str) -> None:
    """Export 2000 and 2024 classified maps to Google Drive."""
    ee.Initialize()
    aoi = ee.Geometry.Rectangle(AOI_BBOX)
    training = ee.FeatureCollection(training_asset)
    for year in (2000, 2024):
        task = ee.batch.Export.image.toDrive(
            image=classify(year, training, aoi),
            description=f"sw_mau_landcover_{year}",
            region=aoi,
            scale=SCALE_M,
            crs=EXPORT_CRS,
            maxPixels=1e10,
        )
        task.start()


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
