from dataclasses import dataclass, field

CITY_OF_VIENNA = "CC BY 4.0, Datenquelle: Stadt Wien – data.wien.gv.at"
WIENER_LINIEN = "CC BY 4.0, Datenquelle: Wiener Linien – data.wien.gv.at"
OPENSTREETMAP = "ODbL, © OpenStreetMap contributors"

WFS_BASE = (
    "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0"
    "&srsName=EPSG:4326&typeName=ogdwien:{layer}&outputFormat={fmt}"
)


@dataclass(frozen=True)
class StatisticsSeries:
    """A district statistics table with the MA 23 layout (title line, header, `9xx00` codes)."""

    key: str
    url: str
    columns: dict[str, str]
    row_filter: dict[str, str] = field(default_factory=dict)
    sum_over: str | None = None
    licence: str = CITY_OF_VIENNA


@dataclass(frozen=True)
class PointLayer:
    key: str
    layer: str
    category: str
    licence: str = CITY_OF_VIENNA

    @property
    def url(self) -> str:
        return WFS_BASE.format(layer=self.layer, fmt="csv")


STATISTICS = [
    StatisticsSeries(
        "density",
        "https://www.wien.gv.at/gogv/l9ogdviebezbizpopden2002f",
        {"POP_VALUE": "population", "AREA": "area_km2", "POP_DENSITY": "population_density"},
    ),
    StatisticsSeries(
        "age",
        "https://www.wien.gv.at/gogv/l9ogdviebezbizpopage2002f",
        {"AGE_AVE": "avg_age"},
    ),
    StatisticsSeries(
        "income",
        "https://www.wien.gv.at/gogv/l9ogdviebezbizecnincsex2002f",
        {"INC_TOT_VALUE": "net_income"},
    ),
    StatisticsSeries(
        "unemployment",
        "https://www.wien.gv.at/gogv/l9ogdviebezbizempsexuep2002f",
        {"UEP_DENSITY": "unemployed_per_1000"},
        row_filter={"SEX": "0"},
    ),
    StatisticsSeries(
        "education",
        "https://www.wien.gv.at/gogv/l9ogdviebezbizeduatt2008f",
        {"EDU_AKA": "pct_tertiary_education"},
    ),
    StatisticsSeries(
        "households",
        "https://www.wien.gv.at/gogv/l9ogdviebezpopsexhhtyp2012f",
        {
            "EPH": "people_single_household",
            "MPH": "people_shared_household",
            "EHE": "people_married_household",
            "LGM": "people_cohabiting_household",
            "V_K": "people_single_father_household",
            "M_K": "people_single_mother_household",
        },
        sum_over="SEX",
    ),
    StatisticsSeries(
        "families",
        "https://www.wien.gv.at/gogv/l9ogdviebezfamtyp2012f",
        {
            "EHE": "families_married_no_children",
            "EHE_K": "families_married_children",
            "LGEM": "families_cohabiting_no_children",
            "LGEM_K": "families_cohabiting_children",
            "V_K": "families_single_father",
            "M_K": "families_single_mother",
        },
    ),
    StatisticsSeries(
        "traffic_area",
        "https://www.wien.gv.at/gogv/l9ogdviebezbiztectra2002f",
        {
            "FAH_VALUE": "road_area_m2",
            "FUS_VALUE": "pedestrian_zone_m2",
            "RAD_KM_VALUE": "cycle_path_km",
        },
    ),
    StatisticsSeries(
        "medical",
        "https://www.wien.gv.at/gogv/l9ogdviebezbizmedsup2002f",
        {
            "ALL_DENSITY": "gps_per_1000",
            "FAC_DENSITY": "specialists_per_1000",
            "APO_DENSITY": "pharmacies_per_1000",
        },
    ),
    StatisticsSeries(
        "tourism",
        "https://www.wien.gv.at/gogv/l9ogdviebezbizecntou2002f",
        {"TOU_DENSITY": "overnight_stays_per_1000"},
    ),
]

CAR_DENSITY_URL = "https://www.wien.gv.at/data/ogd/ma20/pkwdichte2024.csv"

POINT_LAYERS = [
    PointLayer("parks", "PARKINFOOGD", "park"),
    PointLayer("schools", "SCHULEOGD", "school"),
    PointLayer("kindergartens", "KINDERGARTENOGD", "kindergarten"),
    PointLayer("universities", "UNIVERSITAETOGD", "university"),
    PointLayer("markets", "MAERKTEOGD", "market"),
    PointLayer("museums", "MUSEUMOGD", "museum"),
    PointLayer("sport_facilities", "SPORTSTAETTENOGD", "sport_facility"),
    PointLayer("playgrounds", "SPIELPLATZPUNKTOGD", "playground"),
]

DISTRICT_BORDERS_URL = WFS_BASE.format(layer="BEZIRKSGRENZEOGD", fmt="json")

GTFS_URL = "http://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
