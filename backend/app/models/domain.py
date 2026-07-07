from dataclasses import dataclass


@dataclass(frozen=True)
class CropProfile:
    name: str
    seasons: tuple[str, ...]
    soil_types: tuple[str, ...]
    ph_min: float
    ph_max: float
    rainfall_min_mm: int
    rainfall_max_mm: int
    water_need: str
    notes: str


CROP_PROFILES: tuple[CropProfile, ...] = (
    CropProfile(
        name="millet",
        seasons=("kharif", "rabi"),
        soil_types=("red", "sandy", "black", "alluvial"),
        ph_min=5.5,
        ph_max=8.0,
        rainfall_min_mm=300,
        rainfall_max_mm=700,
        water_need="low",
        notes="Good option for low rainfall and marginal land.",
    ),
    CropProfile(
        name="pulses",
        seasons=("kharif", "rabi"),
        soil_types=("black", "red", "alluvial"),
        ph_min=6.0,
        ph_max=7.8,
        rainfall_min_mm=350,
        rainfall_max_mm=800,
        water_need="low",
        notes="Improves soil nitrogen and fits small farms.",
    ),
    CropProfile(
        name="groundnut",
        seasons=("kharif", "summer"),
        soil_types=("red", "sandy", "alluvial"),
        ph_min=6.0,
        ph_max=7.5,
        rainfall_min_mm=500,
        rainfall_max_mm=900,
        water_need="medium",
        notes="Needs well-drained soil and avoids waterlogging.",
    ),
    CropProfile(
        name="maize",
        seasons=("kharif", "rabi"),
        soil_types=("black", "red", "alluvial"),
        ph_min=5.8,
        ph_max=7.8,
        rainfall_min_mm=500,
        rainfall_max_mm=900,
        water_need="medium",
        notes="Responsive to timely irrigation and fertilizer.",
    ),
    CropProfile(
        name="cotton",
        seasons=("kharif",),
        soil_types=("black",),
        ph_min=6.0,
        ph_max=8.0,
        rainfall_min_mm=600,
        rainfall_max_mm=1100,
        water_need="medium",
        notes="Fits deep black soil but requires pest monitoring.",
    ),
    CropProfile(
        name="paddy",
        seasons=("kharif",),
        soil_types=("clay", "alluvial", "black"),
        ph_min=5.5,
        ph_max=7.5,
        rainfall_min_mm=900,
        rainfall_max_mm=1800,
        water_need="high",
        notes="Only recommend when water is reliable.",
    ),
    CropProfile(
        name="tomato",
        seasons=("rabi", "summer"),
        soil_types=("red", "black", "alluvial"),
        ph_min=6.0,
        ph_max=7.5,
        rainfall_min_mm=400,
        rainfall_max_mm=800,
        water_need="medium",
        notes="High value crop; needs disease scouting.",
    ),
    CropProfile(
        name="chilli",
        seasons=("kharif", "rabi"),
        soil_types=("red", "black", "alluvial"),
        ph_min=6.0,
        ph_max=7.5,
        rainfall_min_mm=600,
        rainfall_max_mm=1000,
        water_need="medium",
        notes="Requires pest and leaf curl monitoring.",
    ),
)


WATER_RANK = {"low": 1, "medium": 2, "high": 3}

