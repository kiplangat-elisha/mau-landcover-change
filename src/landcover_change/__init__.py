"""Land-cover change detection and statistics for the South West Mau Forest headwaters."""

CLASSES: dict[int, str] = {
    1: "forest",
    2: "tea and cropland",
    3: "grassland and shrubland",
    4: "settlement and bare",
    5: "water",
}
NODATA = 0
