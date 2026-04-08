import os
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# ── Column mapping from NCES CCD to our schema ────
# These are the actual column names in the CCD file
CCD_COLUMNS = {
    "NCESSCH":   "school_id",
    "SCH_NAME":  "name",
    "STABR":     "state_abbr",
    "LEANM":     "district",
    "LCITY":     "city",
    "NMCNTY":    "county",
    "GSLO":      "grade_low",
    "GSHI":      "grade_high",
    "SCHTYPE":   "school_type_code",
    "CHARTER":   "charter",
    "MAGNET":    "magnet",
    "MEMBER":    "student_count",
    "WEBSITE":   "website",
    "PHONE":     "phone",
}

# State abbreviation to full name
STATE_NAMES = {
    "AL": "Alabama",    "AK": "Alaska",     "AZ": "Arizona",
    "AR": "Arkansas",   "CA": "California", "CO": "Colorado",
    "CT": "Connecticut","DE": "Delaware",   "FL": "Florida",
    "GA": "Georgia",    "HI": "Hawaii",     "ID": "Idaho",
    "IL": "Illinois",   "IN": "Indiana",    "IA": "Iowa",
    "KS": "Kansas",     "KY": "Kentucky",   "LA": "Louisiana",
    "ME": "Maine",      "MD": "Maryland",   "MA": "Massachusetts",
    "MI": "Michigan",   "MN": "Minnesota",  "MS": "Mississippi",
    "MO": "Missouri",   "MT": "Montana",    "NE": "Nebraska",
    "NV": "Nevada",     "NH": "New Hampshire","NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York",   "NC": "North Carolina",
    "ND": "North Dakota","OH": "Ohio",      "OK": "Oklahoma",
    "OR": "Oregon",     "PA": "Pennsylvania","RI": "Rhode Island",
    "SC": "South Carolina","SD": "South Dakota","TN": "Tennessee",
    "TX": "Texas",      "UT": "Utah",       "VT": "Vermont",
    "VA": "Virginia",   "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin",  "WY": "Wyoming",    "DC": "District of Columbia"
}

# Grade range to education level mapping
def grade_to_level(grade_low, grade_high):
    """Map grade range to education level."""
    pk_grades  = ["PK", "KG", "K"]
    elem_high  = ["01", "02", "03", "04", "05", "06",
                  "1",  "2",  "3",  "4",  "5",  "6"]
    mid_grades = ["06", "07", "08", "6", "7", "8"]
    high_grades= ["09", "10", "11", "12", "9", "10", "11", "12"]

    gl = str(grade_low).strip().upper()
    gh = str(grade_high).strip().upper()

    if gl == "PK":
        return "Preschool"
    if gl in ["KG", "K", "01", "1"] and gh in ["05", "06", "5", "6"]:
        return "Elementary"
    if gl in ["06", "07", "6", "7"] and gh in ["08", "8"]:
        return "Middle School"
    if gl in ["09", "9"] and gh in ["12"]:
        return "High School"
    if gl in ["KG", "K"] and gh in ["08", "8"]:
        return "Elementary"
    if gl in ["KG", "K", "01", "1"] and gh == "12":
        return "High School"  # Combined K-12

    # Fallback by grade numbers
    try:
        low_num  = int(gl) if gl.isdigit() else 0
        high_num = int(gh) if gh.isdigit() else 12
        if low_num <= 6 and high_num <= 6:
            return "Elementary"
        if 6 <= low_num <= 8 and high_num <= 8:
            return "Middle School"
        if low_num >= 9:
            return "High School"
    except Exception:
        pass

    return "Elementary"  # Default


def process_ccd_file(
    input_path="data/nces_schools.csv",
    output_path="data/k12_schools.csv",
    sample_size=None
):
    """
    Process the NCES CCD CSV file and convert it
    to our standardized schools.csv format.

    Args:
        input_path: Path to downloaded NCES CCD CSV
        output_path: Where to save processed file
        sample_size: If set, only process N rows (for testing)
    """
    print(f"📂 Loading NCES CCD file: {input_path}")

    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        print("   Please download from:")
        print("   https://nces.ed.gov/ccd/files.asp")
        return None

    # Try different encodings
    for encoding in ["latin-1", "utf-8", "cp1252"]:
        try:
            df = pd.read_csv(
                input_path,
                encoding=encoding,
                low_memory=False,
                nrows=sample_size
            )
            print(f"   ✅ Loaded with {encoding} encoding")
            break
        except Exception as e:
            print(f"   ⚠️ {encoding} failed: {e}")
            continue

    print(f"   📊 Raw rows: {len(df):,}")
    print(f"   📊 Columns: {list(df.columns[:10])}...")

    # Find actual column names (CCD columns vary by year)
    col_map = {}
    for ccd_col, our_col in CCD_COLUMNS.items():
        # Try exact match first
        if ccd_col in df.columns:
            col_map[ccd_col] = our_col
        else:
            # Try case-insensitive match
            for actual_col in df.columns:
                if actual_col.upper() == ccd_col.upper():
                    col_map[actual_col] = our_col
                    break

    print(f"   📊 Mapped columns: {list(col_map.keys())}")

    # Rename columns we found
    df = df.rename(columns=col_map)

    # Keep only active schools
    if "STATUS" in df.columns:
        df = df[df["STATUS"] == 1]
    elif "SY_STATUS" in df.columns:
        df = df[df["SY_STATUS"] == 1]

    print(f"   📊 Active schools: {len(df):,}")

    # Add state full name
    if "state_abbr" in df.columns:
        df["state"] = df["state_abbr"].map(STATE_NAMES)
        df = df.dropna(subset=["state"])
    else:
        print("   ❌ state_abbr column not found")
        return None

    # Determine education level from grade range
    if "grade_low" in df.columns and "grade_high" in df.columns:
        df["level"] = df.apply(
            lambda r: grade_to_level(
                r["grade_low"], r["grade_high"]
            ),
            axis=1
        )
    else:
        df["level"] = "Elementary"

    # School type
    if "school_type_code" in df.columns:
        type_map = {1: "Public", 2: "Public", 3: "Charter"}
        df["type"] = df["school_type_code"].map(type_map).fillna("Public")
    elif "charter" in df.columns:
        df["type"] = df["charter"].apply(
            lambda x: "Charter" if str(x).strip() in ["1", "Y", "Yes"]
            else "Public"
        )
    else:
        df["type"] = "Public"

    # Clean county name
    if "county" in df.columns:
        df["county"] = (
            df["county"]
            .fillna("")
            .astype(str)
            .str.replace(" County", "", regex=False)
            .str.strip()
        )
    else:
        df["county"] = ""

    # Clean other fields
    df["city"]   = df.get("city",  pd.Series([""] * len(df))).fillna("")
    df["name"]   = df.get("name",  pd.Series([""] * len(df))).fillna("")
    df["website"]= df.get("website", pd.Series([""] * len(df))).fillna("")
    df["district"]= df.get("district", pd.Series([""] * len(df))).fillna("")

    # Student count
    if "student_count" in df.columns:
        df["student_count"] = pd.to_numeric(
            df["student_count"], errors="coerce"
        ).fillna(0).astype(int)
    else:
        df["student_count"] = 0

    # Build description
    def build_description(row):
        stype    = row.get("type", "Public")
        level    = row.get("level", "")
        city     = row.get("city", "")
        state    = row.get("state", "")
        district = row.get("district", "")
        students = row.get("student_count", 0)

        desc = f"{stype} {level} school in {city}, {state}."
        if district and district != row.get("name", ""):
            desc += f" Part of {district}."
        if students > 0:
            desc += f" Enrollment: {int(students):,} students."
        return desc

    df["description"] = df.apply(build_description, axis=1)

    # Build final dataframe in our schema
    output_df = pd.DataFrame({
        "school_id":            df["school_id"].astype(str),
        "name":                  df["name"].astype(str),
        "type":                  df["type"].astype(str),
        "level":                 df["level"].astype(str),
        "state":                 df["state"].astype(str),
        "county":                df["county"].astype(str),
        "city":                  df["city"].astype(str),
        "district":              df["district"].astype(str),
        "rating":                0.0,
        "tuition_min":           0,
        "tuition_max":           0,
        "student_count":         df["student_count"],
        "teacher_student_ratio": "N/A",
        "ap_courses":            0,
        "clubs":                 0,
        "application_deadline":  "Contact school",
        "website":               df["website"].astype(str),
        "application_fee":       0,
        "description":           df["description"].astype(str),
    })

    # Remove rows with no name
    output_df = output_df[output_df["name"].str.len() > 2]
    output_df = output_df.reset_index(drop=True)

    print(f"\n✅ Processed {len(output_df):,} schools")
    print(f"   States: {output_df['state'].nunique()}")
    print(f"   Levels: {output_df['level'].value_counts().to_dict()}")

    # Show sample by state
    print("\n   Sample by state:")
    state_counts = output_df["state"].value_counts().head(10)
    for state, count in state_counts.items():
        print(f"   {state}: {count:,} schools")

    # Save
    output_df.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    return output_df


def get_k12_by_state_level(
    state, level, county=None,
    csv_path="data/k12_schools.csv",
    limit=50
):
    """
    Query the local K-12 database by state, level,
    and optionally county.
    Returns list of school dicts.
    """
    if not os.path.exists(csv_path):
        print(f"   ⚠️ K-12 database not found: {csv_path}")
        return []

    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        print(f"   ❌ Error reading K-12 DB: {e}")
        return []

    # Filter
    mask = (
        (df["state"] == state) &
        (df["level"] == level)
    )
    filtered = df[mask]

    # Apply county filter
    if county and county not in ["All Counties", "Select County", ""]:
        county_clean = county.replace(" County", "").strip()
        filtered = filtered[
            filtered["county"].str.contains(
                county_clean, case=False, na=False
            )
        ]

    # Sort by student count descending
    filtered = filtered.sort_values(
        "student_count", ascending=False
    ).head(limit)

    return filtered.to_dict("records")


if __name__ == "__main__":
    print("=" * 55)
    print("   NCES CCD Database Builder")
    print("=" * 55)

    # Test with sample first
    print("\n🔍 Testing with sample of 1000 rows...")
    sample_df = process_ccd_file(
        input_path  = "data/nces_schools.csv",
        output_path = "data/k12_schools_sample.csv",
        sample_size = 1000
    )

    if sample_df is not None:
        print("\n✅ Sample test passed!")
        print("   Ready to process full file.")
        print("\n   Run full processing? Edit this file and")
        print("   remove sample_size=1000 parameter.")
    else:
        print("\n❌ Please download the NCES CCD file first.")
        print("   https://nces.ed.gov/ccd/files.asp")