import os
import pandas as pd

ALL_US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

STATE_LEVEL_EDUCATION  = ["University", "Community College", "Medical School"]
COUNTY_LEVEL_EDUCATION = ["High School", "Elementary", "Preschool", "Middle School"]


def load_geo_data(csv_path="data/schools.csv"):
    return pd.read_csv(csv_path)


def get_all_states():
    return ALL_US_STATES


def get_education_levels():
    return [
        "Preschool",
        "Elementary",
        "Middle School",
        "High School",
        "Community College",
        "University",
        "Medical School"
    ]


def is_county_applicable(level):
    return level in COUNTY_LEVEL_EDUCATION


def is_city_applicable(level):
    return True


def has_local_data(df, state, level):
    filtered = df[
        (df["state"] == state) &
        (df["level"] == level)
    ]
    return len(filtered) > 0


def _get_search_levels(level):
    """
    Return levels to search in k12 database.
    Elementary includes Preschool because many
    elementary schools offering Pre-K are classified
    as Prekindergarten in NCES CCD data.
    Example: MINETT EL (Frisco ISD) is classified
    as Preschool in NCES but is an elementary school.
    """
    if level == "Elementary":
        return ["Elementary", "Preschool"]
    return [level]


def get_counties_for_level(df, state, level):
    """
    Return districts/counties for K-12 filtering.
    Uses district from k12_schools.csv (more meaningful),
    falls back to county, then schools.csv.
    """
    if not is_county_applicable(level):
        return []
    if not state or state == "Select State":
        return []

    k12_path = "data/k12_schools.csv"
    if os.path.exists(k12_path):
        try:
            k12_df = pd.read_csv(
                k12_path,
                usecols    = ["state", "level", "district", "county"],
                low_memory = False
            )
            for col in ["state", "level", "district", "county"]:
                k12_df[col] = (
                    k12_df[col].fillna("").astype(str)
                    .replace({"nan": "", "None": ""})
                )

            # Use expanded level search for Elementary
            search_levels = _get_search_levels(level)
            filtered = k12_df[
                (k12_df["state"] == state) &
                (k12_df["level"].isin(search_levels))
            ]

            # Try district first — more meaningful than county
            districts = sorted([
                d for d in filtered["district"].unique()
                if d.strip() and d not in ["nan", "None"]
            ])
            if districts:
                return districts

            # Fall back to county
            counties = sorted([
                c for c in filtered["county"].unique()
                if c.strip() and c not in ["nan", "None"]
            ])
            if counties:
                return counties

        except Exception:
            pass

    # Final fallback to schools.csv
    filtered = df[
        (df["state"] == state) &
        (df["level"] == level)
    ]
    return sorted(
        filtered["county"].dropna().unique().tolist()
    )


def get_cities_for_county(state, level, district=None):
    """
    Return sorted cities for given state/level/district.
    Uses exact district match to avoid ALLEN matching MCALLEN.
    Elementary includes Preschool-classified schools.
    """
    k12_path = "data/k12_schools.csv"
    if not os.path.exists(k12_path):
        return []

    try:
        k12_df = pd.read_csv(
            k12_path,
            usecols    = ["state", "level", "district", "county", "city"],
            low_memory = False
        )
        for col in ["state", "level", "district", "county", "city"]:
            k12_df[col] = (
                k12_df[col].fillna("").astype(str)
                .replace({"nan": "", "None": ""})
            )

        # Use expanded level search for Elementary
        search_levels = _get_search_levels(level)

        mask = (
            (k12_df["state"] == state) &
            (k12_df["level"].isin(search_levels)) &
            (k12_df["city"]  != "")
        )

        if district and district not in [
            "All Districts", "All Counties",
            "Select District", ""
        ]:
            # Exact match — prevents ALLEN matching MCALLEN/CALALLEN
            dist_mask = (
                (k12_df["district"].str.strip().str.upper() ==
                 district.strip().upper()) |
                (k12_df["county"].str.strip().str.upper() ==
                 district.strip().upper())
            )
            mask = mask & dist_mask

        cities = sorted(
            k12_df[mask]["city"]
            .str.title()
            .unique()
            .tolist()
        )
        return cities

    except Exception:
        return []


def get_cities_for_university(state, level):
    """
    Return sorted cities for university levels
    by fetching from College Scorecard API.
    """
    from utils.college_scorecard_api import fetch_universities
    try:
        schools = fetch_universities(state, level, per_page=100)
        cities  = sorted(set(
            s["city"].strip().title()
            for s in schools
            if s.get("city", "").strip()
        ))
        return cities
    except Exception:
        return []


def filter_schools(
    df, state=None, level=None,
    county=None, city=None
):
    """Apply filters to schools.csv dataframe."""
    filtered = df.copy()

    if level and level != "Select Level":
        filtered = filtered[filtered["level"] == level]
    if state and state != "Select State":
        filtered = filtered[filtered["state"] == state]

    if is_county_applicable(level):
        if county and county not in [
            "Select County", "All Counties",
            "All Districts", "Select District", ""
        ]:
            # Exact match to avoid partial matches
            filtered = filtered[
                filtered["county"].str.strip().str.upper() ==
                county.strip().upper()
            ]
        if city and city not in ["All Cities", ""]:
            # Exact match to avoid Allen matching McAllen
            filtered = filtered[
                filtered["city"].str.strip().str.upper() ==
                city.strip().upper()
            ]

    return filtered.reset_index(drop=True)


def get_filter_summary(
    state, level, county=None, city=None
):
    """Human-readable filter summary."""
    if not state or not level:
        return "Please select filters to begin."

    if is_county_applicable(level):
        parts = []
        if city and city not in ["All Cities", ""]:
            parts.append(city)
        if county and county not in [
            "All Counties", "All Districts", ""
        ]:
            parts.append(county)
        parts.append(state)
        return f"Showing {level} schools in {', '.join(parts)}"

    return f"Showing {level} institutions in {state}"