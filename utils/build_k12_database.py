import os
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# ── Path Configuration ─────────────────────────────
INPUT_PATH    = "data/nces_schools.csv"
OUTPUT_PATH   = "data/k12_schools.csv"
ZIP_COUNTY_DB = "data/zip_county.csv"

# ── ZIP to County cache ────────────────────────────
_zip_county_map = None


def load_zip_county_map():
    """Load ZIP to county mapping once and cache it."""
    global _zip_county_map
    if _zip_county_map is not None:
        return _zip_county_map

    if not os.path.exists(ZIP_COUNTY_DB):
        print(f"   ⚠️ ZIP county DB not found: {ZIP_COUNTY_DB}")
        _zip_county_map = {}
        return _zip_county_map

    try:
        zip_df = pd.read_csv(
            ZIP_COUNTY_DB,
            dtype       = {"zip": str},
            usecols     = ["zip", "county"]
        )
        _zip_county_map = dict(
            zip(zip_df["zip"].str.zfill(5), zip_df["county"])
        )
        print(f"   ✅ ZIP county map loaded: "
              f"{len(_zip_county_map):,} ZIPs")
    except Exception as e:
        print(f"   ⚠️ ZIP county load error: {e}")
        _zip_county_map = {}

    return _zip_county_map


def get_county_from_zip(zip_code):
    """Look up county name from ZIP code."""
    zmap     = load_zip_county_map()
    zip_clean = str(zip_code or "").strip()[:5].zfill(5)
    county   = zmap.get(zip_clean, "")
    # Clean up county name
    county   = county.replace(" County", "").strip()
    if county.lower() in ["nan", "none", ""]:
        return ""
    return county


# ── Exact column names from NCES 2022-23 file ─────
CCD_COLUMN_CANDIDATES = {
    "school_id":    ["NCESSCH", "ncessch"],
    "name":         ["SCH_NAME", "sch_name"],
    "state_abbr":   ["ST", "STABR", "stabr"],
    "district":     ["LEA_NAME", "leanm", "LEANM"],
    "city":         ["LCITY", "lcity"],
    "county":       [],           # Not in directory file
    "grade_low":    ["GSLO", "gslo"],
    "grade_high":   ["GSHI", "gshi"],
    "level":        ["LEVEL"],    # Already computed by NCES!
    "school_type":  ["SCH_TYPE",  "sch_type"],
    "charter":      ["CHARTER_TEXT", "charter_text"],
    "magnet":       [],           # Not in directory file
    "student_count":[],           # Not in directory file
    "website":      ["WEBSITE",   "website"],
    "status":       ["SY_STATUS", "sy_status"],
    "zip":          ["LZIP",      "lzip"],
    "street":       ["LSTREET1",  "lstreet1"],
    "state_name":   ["STATENAME", "statename"],
}

# ── State abbreviation to full name ───────────────
STATE_NAMES = {
    "AL": "Alabama",         "AK": "Alaska",
    "AZ": "Arizona",         "AR": "Arkansas",
    "CA": "California",      "CO": "Colorado",
    "CT": "Connecticut",     "DE": "Delaware",
    "FL": "Florida",         "GA": "Georgia",
    "HI": "Hawaii",          "ID": "Idaho",
    "IL": "Illinois",        "IN": "Indiana",
    "IA": "Iowa",            "KS": "Kansas",
    "KY": "Kentucky",        "LA": "Louisiana",
    "ME": "Maine",           "MD": "Maryland",
    "MA": "Massachusetts",   "MI": "Michigan",
    "MN": "Minnesota",       "MS": "Mississippi",
    "MO": "Missouri",        "MT": "Montana",
    "NE": "Nebraska",        "NV": "Nevada",
    "NH": "New Hampshire",   "NJ": "New Jersey",
    "NM": "New Mexico",      "NY": "New York",
    "NC": "North Carolina",  "ND": "North Dakota",
    "OH": "Ohio",            "OK": "Oklahoma",
    "OR": "Oregon",          "PA": "Pennsylvania",
    "RI": "Rhode Island",    "SC": "South Carolina",
    "SD": "South Dakota",    "TN": "Tennessee",
    "TX": "Texas",           "UT": "Utah",
    "VT": "Vermont",         "VA": "Virginia",
    "WA": "Washington",      "WV": "West Virginia",
    "WI": "Wisconsin",       "WY": "Wyoming",
    "DC": "District of Columbia",
    "PR": "Puerto Rico",
}

# ── NCES LEVEL column values ───────────────────────
# 1=Elementary, 2=Middle, 3=High, 4=Other
NCES_LEVEL_MAP = {
    # Text values (actual values in 2022-23 file)
    "Elementary":       "Elementary",
    "Middle":           "Middle School",
    "High":             "High School",
    "Secondary":        "High School",
    "Prekindergarten":  "Preschool",
    "Other":            "Elementary",
    "Not reported":     "Elementary",
    "Not applicable":   "Elementary",
    "Ungraded":         "Elementary",
    "Adult Education":  "Elementary",
    # Numeric values (older file versions)
    "1":    "Elementary",
    "2":    "Middle School",
    "3":    "High School",
    "4":    "Elementary",
    "1.0":  "Elementary",
    "2.0":  "Middle School",
    "3.0":  "High School",
    "4.0":  "Elementary",
}


def find_column(df, candidates):
    """Find first matching column from candidates list."""
    for col in candidates:
        if col in df.columns:
            return col
    # Case-insensitive fallback
    upper_map = {c.upper(): c for c in df.columns}
    for col in candidates:
        if col.upper() in upper_map:
            return upper_map[col.upper()]
    return None


def nces_level_to_our_level(nces_level, grade_low):
    """
    Convert NCES LEVEL code to our education level.
    Uses grade_low to detect Preschool since NCES
    codes PK as Level 1 (Elementary).
    """
    # Check for Preschool via grade_low first
    gl = str(grade_low or "").strip().upper()
    if gl == "PK":
        return "Preschool"

    # Use NCES level code
    level_str = str(nces_level or "").strip()
    if level_str in NCES_LEVEL_MAP:
        return NCES_LEVEL_MAP[level_str]

    # Fallback grade calculation
    return grade_to_level(grade_low, "")


def grade_to_level(grade_low, grade_high):
    """Fallback: map grade range to education level."""
    gl = str(grade_low  or "").strip().upper()
    gh = str(grade_high or "").strip().upper()

    if gl == "PK":
        return "Preschool"
    if gl in ["KG", "K", "01", "02", "1", "2"] and \
       gh in ["04", "05", "06", "4", "5", "6", "03", "3"]:
        return "Elementary"
    if gl in ["06", "07", "6", "7"] and \
       gh in ["08", "09", "8", "9"]:
        return "Middle School"
    if gl in ["09", "10", "9", "10"] and gh == "12":
        return "High School"
    if gl in ["KG", "K", "01", "1"] and gh == "12":
        return "High School"
    return "Elementary"


def build_description(
    stype, level, city, state,
    county="", district=""
):
    """Build clean school description."""
    level_map = {
        "Elementary":    "elementary",
        "Middle School": "middle",
        "High School":   "high",
        "Preschool":     "preschool",
    }
    level_word = level_map.get(level, level.lower())

    loc_parts = []
    if city and city not in ["nan", "None", ""]:
        loc_parts.append(city)
    if county and county not in ["nan", "None", ""]:
        loc_parts.append(f"{county} County")
    if state and state not in ["nan", "None", ""]:
        loc_parts.append(state)
    location = ", ".join(loc_parts) if loc_parts else state

    desc = f"{stype} {level_word} school in {location}."
    if (district and
            district not in ["nan", "None", ""] and
            district != ""):
        desc += f" Part of {district}."

    return desc


def process_ccd_file(
    input_path  = INPUT_PATH,
    output_path = OUTPUT_PATH,
    sample_size = None
):
    """
    Process NCES CCD CSV file into our standardized schema.
    """
    print(f"\n📂 Loading: {input_path}")

    if not os.path.exists(input_path):
        print(f"\n❌ File not found: {input_path}")
        print("   Download from: https://nces.ed.gov/ccd/files.asp")
        return None

    # ── Load file ──────────────────────────────────
    df = None
    for encoding in ["latin-1", "utf-8", "cp1252"]:
        try:
            df = pd.read_csv(
                input_path,
                encoding   = encoding,
                low_memory = False,
                nrows      = sample_size
            )
            print(f"   ✅ Loaded with {encoding} encoding")
            print(f"   📊 Rows: {len(df):,} | "
                  f"Columns: {len(df.columns)}")
            break
        except Exception:
            continue

    if df is None:
        print("   ❌ Could not load file.")
        return None

    # ── Map columns ────────────────────────────────
    print("\n🔄 Mapping columns...")
    col_refs = {}
    for field, candidates in CCD_COLUMN_CANDIDATES.items():
        found = find_column(df, candidates)
        col_refs[field] = found
        status = f"✅ {found}" if found else "❌ Not found"
        print(f"   {field:<20} → {status}")

    # Check required columns
    required = ["school_id", "name", "state_abbr"]
    missing  = [f for f in required if not col_refs.get(f)]
    if missing:
        print(f"\n❌ Missing required columns: {missing}")
        return None

    # ── Filter active schools ──────────────────────
    print("\n🔄 Filtering active schools...")
    status_col = col_refs.get("status")
    if status_col:
        before = len(df)
        df     = df[df[status_col].astype(str).isin(
            ["1", "1.0"]
        )]
        print(f"   Active: {len(df):,} "
              f"(removed {before - len(df):,})")

    # ── Load ZIP county map ────────────────────────
    print("\n🔄 Loading ZIP to county mapping...")
    load_zip_county_map()

    # ── Process records ────────────────────────────
    print("\n🔄 Building school records...")
    output_records = []

    for _, row in df.iterrows():

        # Required fields
        school_id = str(
            row[col_refs["school_id"]] or ""
        ).strip()
        name = str(
            row[col_refs["name"]] or ""
        ).strip()
        if not name or name in ["nan", "None", ""]:
            continue

        state_abbr = str(
            row[col_refs["state_abbr"]] or ""
        ).strip()
        state = STATE_NAMES.get(state_abbr, "")
        if not state:
            continue

        # Optional fields with safe extraction
        def safe_str(col_key, default=""):
            col = col_refs.get(col_key)
            if not col:
                return default
            val = str(row.get(col, "") or "").strip()
            return "" if val in [
                "nan", "None", "NaN", "none"
            ] else val

        district = safe_str("district")
        city      = safe_str("city")
        zip_code  = safe_str("zip")
        grade_low = safe_str("grade_low")
        grade_high= safe_str("grade_high")
        nces_level= safe_str("nces_level")
        website   = safe_str("website")

        # Clean website
        if website and not website.startswith("http"):
            website = "https://" + website

        # County from ZIP
        county = ""
        if zip_code:
            county = get_county_from_zip(zip_code)

        # Education level
        level = nces_level_to_our_level(
            nces_level, grade_low
        )

        # School type
        stype = "Public"
        sch_type_val = safe_str("school_type")
        charter_val  = safe_str("charter").upper()

        if charter_val in ["YES", "Y", "1", "TRUE"]:
            stype = "Charter"
        elif sch_type_val in ["2", "2.0"]:
            stype = "Special Ed"
        elif sch_type_val in ["3", "3.0"]:
            stype = "Vocational"

        # Build description
        description = build_description(
            stype    = stype,
            level    = level,
            city     = city,
            state    = state,
            county   = county,
            district = district
        )

        output_records.append({
            "school_id":            school_id,
            "name":                  name,
            "type":                  stype,
            "level":                 level,
            "state":                 state,
            "county":                county,
            "city":                  city,
            "district":              district,
            "zip":                   zip_code,
            "rating":                0.0,
            "tuition_min":           0,
            "tuition_max":           0,
            "student_count":         0,
            "teacher_student_ratio": "N/A",
            "ap_courses":            0,
            "clubs":                 0,
            "application_deadline":  "Contact school",
            "website":               website,
            "application_fee":       0,
            "description":           description,
        })

    # ── Build output dataframe ─────────────────────
    output_df = pd.DataFrame(output_records)

    # Ensure string columns are clean
    str_cols = [
        "name", "type", "level", "state", "county",
        "city", "district", "website", "description"
    ]
    for col in str_cols:
        if col in output_df.columns:
            output_df[col] = (
                output_df[col]
                .fillna("")
                .astype(str)
                .replace({"nan": "", "None": ""})
            )

    output_df = output_df[
        output_df["name"].str.len() > 2
    ].reset_index(drop=True)

    # ── Print summary ──────────────────────────────
    print(f"\n✅ Total schools: {len(output_df):,}")

    print(f"\n📊 By State (top 10):")
    for state, count in (
        output_df["state"].value_counts().head(10).items()
    ):
        print(f"   {state:<25} {count:>6,}")

    print(f"\n📊 By Education Level:")
    for level, count in (
        output_df["level"].value_counts().items()
    ):
        print(f"   {level:<20} {count:>6,}")

    print(f"\n📊 By School Type:")
    for stype, count in (
        output_df["type"].value_counts().items()
    ):
        print(f"   {stype:<20} {count:>6,}")

    # County coverage stats
    has_county = output_df[output_df["county"] != ""]
    print(f"\n📊 County data coverage:")
    print(f"   Schools with county: "
          f"{len(has_county):,} / {len(output_df):,} "
          f"({len(has_county)*100//len(output_df)}%)")

    print(f"\n📋 Sample records:")
    sample = output_df[
        output_df["county"] != ""
    ].sample(min(5, len(output_df)))
    for _, row in sample.iterrows():
        print(
            f"   {row['name'][:40]:<40} | "
            f"{row['level']:<15} | "
            f"{row['county']:<15} | "
            f"{row['state']}"
        )

    # ── Save ───────────────────────────────────────
    os.makedirs("data", exist_ok=True)
    output_df.to_csv(output_path, index=False)
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"\n💾 Saved: {output_path} ({size_mb:.1f} MB)")

    return output_df


def get_k12_by_state_level(
    state,
    level,
    county   = None,
    csv_path = OUTPUT_PATH,
    limit    = 50
):
    """
    Query the local K-12 database by state + level.
    Optionally filter by county.
    Returns list of school dicts.
    """
    if not os.path.exists(csv_path):
        return []

    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        print(f"   ❌ Error reading K-12 DB: {e}")
        return []

    # Ensure string types
    for col in ["state", "level", "county", "name"]:
        if col in df.columns:
            df[col] = (
                df[col].fillna("").astype(str)
                .replace({"nan": "", "None": ""})
            )

    # Filter by state and level
    filtered = df[
        (df["state"] == state) &
        (df["level"] == level)
    ].copy()

    if filtered.empty:
        return []

    # County filter
    if county and county not in [
        "All Counties", "Select County", "", "None"
    ]:
        county_clean    = (
            county.replace(" County", "").strip()
        )
        county_mask     = filtered["county"].str.contains(
            county_clean, case=False, na=False
        )
        county_filtered = filtered[county_mask]
        if not county_filtered.empty:
            filtered = county_filtered

    # Sort by name
    filtered = (
        filtered.sort_values("name")
        .head(limit)
        .reset_index(drop=True)
    )

    schools = []
    for _, row in filtered.iterrows():
        name = str(row.get("name", "") or "")
        if not name or name == "nan":
            continue

        def clean(val):
            s = str(val or "")
            return "" if s in [
                "nan", "None", "none", "NaN"
            ] else s

        website = clean(row.get("website", ""))
        if website and not website.startswith("http"):
            website = "https://" + website

        schools.append({
            "school_id":            clean(row.get("school_id", "")),
            "name":                  name,
            "type":                  clean(row.get("type", "Public")),
            "level":                 level,
            "state":                 state,
            "county":                clean(row.get("county", "")),
            "city":                  clean(row.get("city",   "")),
            "district":              clean(row.get("district", "")),
            "rating":                0.0,
            "tuition_min":           0,
            "tuition_max":           0,
            "student_count":         0,
            "teacher_student_ratio": "N/A",
            "ap_courses":            0,
            "clubs":                 0,
            "application_deadline":  "Contact school",
            "website":               website,
            "application_fee":       0,
            "description":           clean(row.get("description", "")),
            "source":               "NCES CCD 2022-23",
        })

    return schools


if __name__ == "__main__":
    print("=" * 55)
    print("   NCES CCD Database Builder")
    print("=" * 55)

    # ── Step 0: Download ZIP county map ───────────
    if not os.path.exists(ZIP_COUNTY_DB):
        print("\n📥 Step 0: Downloading ZIP to county map...")
        try:
            import requests
            from io import StringIO

            url = (
                "https://raw.githubusercontent.com/"
                "scpike/us-state-county-zip/master/"
                "geo-data.csv"
            )
            resp = requests.get(url, timeout=30)

            if resp.status_code == 200:
                zip_df = pd.read_csv(StringIO(resp.text))
                zip_df.columns = [
                    c.lower() for c in zip_df.columns
                ]

                # Find zip and county columns
                zip_col    = next(
                    (c for c in zip_df.columns
                     if "zip" in c), None
                )
                county_col = next(
                    (c for c in zip_df.columns
                     if "county" in c), None
                )

                if zip_col and county_col:
                    result = zip_df[
                        [zip_col, county_col]
                    ].copy()
                    result.columns = ["zip", "county"]
                    result["zip"] = (
                        result["zip"]
                        .astype(str)
                        .str.zfill(5)
                    )
                    result = result.drop_duplicates("zip")
                    result.to_csv(
                        ZIP_COUNTY_DB, index=False
                    )
                    print(
                        f"   ✅ ZIP map saved: "
                        f"{len(result):,} ZIPs"
                    )
                else:
                    print("   ⚠️ ZIP/county columns not found")
            else:
                print(
                    f"   ⚠️ Download failed: "
                    f"{resp.status_code}"
                )
        except Exception as e:
            print(f"   ⚠️ ZIP download error: {e}")
            print("   Continuing without county data...")
    else:
        print(f"\n✅ Step 0: ZIP county map exists.")

    # ── Step 1: Sample test ────────────────────────
    print("\n🔍 Step 1: Sample test (1000 rows)...")
    sample_df = process_ccd_file(
        input_path  = INPUT_PATH,
        output_path = "data/k12_schools_sample.csv",
        sample_size = 1000
    )

    if sample_df is not None:
        print("\n✅ Sample passed!")

        # ── Step 2: Full file ──────────────────────
        print("\n🔄 Step 2: Processing full file...")
        full_df = process_ccd_file(
            input_path  = INPUT_PATH,
            output_path = OUTPUT_PATH,
            sample_size = None
        )

        if full_df is not None:
            print("\n" + "=" * 55)
            print("✅ DATABASE BUILD COMPLETE!")
            print(f"   Schools : {len(full_df):,}")
            print(f"   Output  : {OUTPUT_PATH}")
            print("=" * 55)

            # ── Step 3: Query tests ────────────────
            print("\n🔍 Step 3: Query tests...")
            tests = [
                ("Texas",    "High School", None),
                ("Alaska",   "Elementary",  None),
                ("Alabama",  "Elementary",  None),
                ("Ohio",     "High School", None),
                ("Texas",    "High School", "Collin"),
                ("Texas",    "High School", "Dallas"),
                ("New York", "High School", None),
                ("Florida",  "Elementary",  None),
            ]
            for state, level, county in tests:
                results = get_k12_by_state_level(
                    state, level, county, limit=3
                )
                county_str = (
                    f" ({county} County)"
                    if county else ""
                )
                print(
                    f"\n   {level} in "
                    f"{state}{county_str}:"
                )
                if results:
                    for r in results:
                        print(
                            f"   → {r['name'][:42]:<42}"
                            f" | {r['county']:<15}"
                            f" | {r['city']}"
                        )
                else:
                    print("   → No results found")