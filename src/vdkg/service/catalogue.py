"""User-facing vocabulary: preferences users can choose and labels for the features behind them."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Preference:
    id: str
    label: str
    group: str
    description: str


PREFERENCES = (
    Preference(
        "going_out", "Going out", "Going out", "Bars, pubs and clubs within walking distance"
    ),
    Preference("food", "Restaurants & cafés", "Going out", "Many places to eat and drink coffee"),
    Preference("culture", "Culture", "Going out", "Museums and a lively city atmosphere"),
    Preference("sport_tennis", "Tennis", "Sports", "Tennis courts and clubs"),
    Preference("sport_football", "Football", "Sports", "Football pitches and cages"),
    Preference("sport_basketball", "Basketball", "Sports", "Basketball courts"),
    Preference(
        "sport_volleyball", "Volleyball", "Sports", "Volleyball and beach volleyball courts"
    ),
    Preference("sport_fitness", "Fitness", "Sports", "Gyms and outdoor fitness stations"),
    Preference("sport_swimming", "Swimming", "Sports", "Public pools and baths"),
    Preference(
        "green_quiet", "Green & quiet", "Everyday life", "Parks, low density, little traffic"
    ),
    Preference(
        "family", "Family-friendly", "Everyday life", "Kindergartens, playgrounds, families"
    ),
    Preference(
        "students", "Student life", "Everyday life", "Universities, young residents, nightlife"
    ),
    Preference("healthcare", "Healthcare", "Everyday life", "Doctors and pharmacies close by"),
    Preference("well_connected", "Well connected", "Mobility", "U-Bahn access, fast to the centre"),
    Preference("car_free", "Car-free living", "Mobility", "Few cars, cycle paths, dense transit"),
)
PREFERENCE_BY_ID = {p.id: p for p in PREFERENCES}

FEATURE_LABELS = {
    "nightlife_per_km2": "Bars, pubs & clubs per km²",
    "food_per_km2": "Restaurants & cafés per km²",
    "museums": "Museums",
    "universities": "University sites",
    "kindergartens_per_10k": "Kindergartens per 10,000 residents",
    "schools_per_10k": "Schools per 10,000 residents",
    "playgrounds_per_10k": "Playgrounds per 10,000 residents",
    "tennis_per_10k": "Tennis venues per 10,000 residents",
    "football_per_10k": "Football venues per 10,000 residents",
    "basketball_per_10k": "Basketball venues per 10,000 residents",
    "volleyball_per_10k": "Volleyball venues per 10,000 residents",
    "fitness_per_10k": "Fitness venues per 10,000 residents",
    "swimming_per_10k": "Swimming venues per 10,000 residents",
    "park_share": "Share of area covered by parks",
    "population_density": "Residents per km²",
    "road_share": "Share of area used by roads",
    "cycle_km_per_km2": "Cycle paths (km per km²)",
    "single_household_share": "Residents living alone",
    "families_with_children_share": "Families with children",
    "avg_age": "Average age",
    "net_income": "Average net income (€/year)",
    "unemployed_per_1000": "Unemployed per 1,000 residents",
    "pct_tertiary_education": "Residents with tertiary education (%)",
    "cars_per_1000": "Cars per 1,000 residents",
    "gps_per_1000": "General practitioners per 1,000 residents",
    "specialists_per_1000": "Medical specialists per 1,000 residents",
    "pharmacies_per_1000": "Pharmacies per 1,000 residents",
    "overnight_stays_per_1000": "Tourist overnight stays per 1,000 residents",
    "subway_lines": "U-Bahn lines",
    "stations_per_km2": "Public transport stops per km²",
    "minutes_to_centre": "Minutes to the city centre",
}
