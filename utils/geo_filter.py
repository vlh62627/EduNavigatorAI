import pandas as pd
import os

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


def get_counties_for_level(df, state, level):
    """
    Return counties — checks k12_schools.csv first
    for NCES data, falls back to local schools.csv.
    """
    if not is_county_applicable(level):
        return []
    if not state or state == "Select State":
        return []

    # Try NCES k12 database first
    k12_path = "data/k12_schools.csv"
    if os.path.exists(k12_path):
        try:
            k12_df = pd.read_csv(
                k12_path,
                usecols=["state", "level", "county"],
                low_memory=False
            )
            k12_df["county"] = (
                k12_df["county"].fillna("").astype(str)
                .replace({"nan": "", "None": ""})
            )
            filtered = k12_df[
                (k12_df["state"] == state) &
                (k12_df["level"] == level) &
                (k12_df["county"] != "")
            ]
            counties = sorted(
                filtered["county"].unique().tolist()
            )
            if counties:
                return counties
        except Exception:
            pass

    # Fallback to schools.csv
    filtered = df[
        (df["state"] == state) &
        (df["level"] == level)
    ]
    return sorted(
        filtered["county"].dropna().unique().tolist()
    )


def has_local_data(df, state, level):
    """
    Check if local database has any data
    for the given state and level combination.
    """
    filtered = df[
        (df["state"] == state) &
        (df["level"] == level)
    ]
    return len(filtered) > 0


def filter_schools(df, state=None, level=None, county=None):
    """
    Apply filters. Returns empty dataframe
    (not None) if no local data exists —
    this signals the Orchestrator to use
    the Researcher Agent instead.
    """
    filtered = df.copy()

    if level and level != "Select Level":
        filtered = filtered[filtered["level"] == level]

    if state and state != "Select State":
        filtered = filtered[filtered["state"] == state]

    if is_county_applicable(level):
        if county and county not in ["Select County", "All Counties"]:
            filtered = filtered[filtered["county"] == county]

    return filtered.reset_index(drop=True)


def get_filter_summary(state, level, county=None):
    if not state or not level:
        return "Please select filters to begin."
    if is_county_applicable(level):
        if county and county not in ["Select County", "All Counties"]:
            return f"Showing {level} schools in {county} County, {state}"
        return f"Showing {level} schools in {state} (all counties)"
    return f"Showing {level} institutions in {state}"