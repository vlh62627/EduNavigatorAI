import os
import re
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

tavily      = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
K12_DB_PATH = "data/k12_schools.csv"


def fetch_k12_schools(
    state, level, county=None, city=None, limit=100
):
    """
    Fetch K-12 schools.
    Priority:
        1. Local NCES CCD database (data/k12_schools.csv)
        2. Tavily web search fallback
    """
    print(f"\n🏫 K-12 Search: {level} in {state}...")

    if os.path.exists(K12_DB_PATH):
        local_results = _get_from_local_db(
            state, level, county, city, limit
        )
        if local_results:
            print(f"   ✅ Local DB: {len(local_results)} schools.")
            return local_results
        else:
            print("   ⚠️ No local results. Using web search...")
    else:
        print("   ℹ️ Local DB not found. Using web search...")

    return _tavily_k12_search(state, level, county, limit)


def _get_search_levels(level):
    """
    Expand level for NCES search.
    Elementary includes Preschool because many elementary
    schools offering Pre-K are classified as Preschool
    in NCES CCD. Example: MINETT EL (Frisco ISD).
    """
    if level == "Elementary":
        return ["Elementary", "Preschool"]
    return [level]


def _get_from_local_db(
    state, level, county=None, city=None, limit=100
):
    """Query local NCES CCD CSV database."""
    try:
        import pandas as pd
        df = pd.read_csv(K12_DB_PATH, low_memory=False)
    except Exception as e:
        print(f"   ❌ DB read error: {e}")
        return []

    # Ensure string types
    for col in ["state", "level", "county", "district", "city", "name"]:
        if col in df.columns:
            df[col] = (
                df[col].fillna("").astype(str)
                .replace({"nan": "", "None": ""})
            )

    # ── Step 1: Base filter by state + level ──────
    search_levels = _get_search_levels(level)
    filtered = df[
        (df["state"] == state) &
        (df["level"].isin(search_levels))
    ].copy()

    # ── Step 2: Always add STEAM/STEM schools ─────
    # STEAM schools in NCES are often classified as
    # Preschool regardless of actual grade range.
    # Always include them so they show under any level.
    steam_df = df[
        (df["state"] == state) &
        (df["name"].str.contains(
            "STEAM|STEM", case=False, na=False
        ))
    ].copy()

    if not steam_df.empty:
        filtered = pd.concat(
            [filtered, steam_df]
        ).drop_duplicates(
            subset=["school_id"] if "school_id" in df.columns
            else ["name"]
        )

    if filtered.empty:
        return []

    # ── Step 3: District filter — exact match ─────
    # Exact match prevents ALLEN ISD matching MCALLEN ISD
    if county and county not in [
        "All Counties", "All Districts",
        "Select County", "Select District", "", "None"
    ]:
        dist_mask = (
            (filtered["district"].str.strip().str.upper() ==
             county.strip().upper()) |
            (filtered["county"].str.strip().str.upper() ==
             county.strip().upper())
        )
        dist_filtered = filtered[dist_mask]
        if not dist_filtered.empty:
            filtered = dist_filtered

    # ── Step 4: City filter — exact match ─────────
    # Exact match prevents Allen matching McAllen
    if city and city not in ["All Cities", "Select City", ""]:
        city_mask = (
            filtered["city"].str.strip().str.upper() ==
            city.strip().upper()
        )
        city_filtered = filtered[city_mask]
        if not city_filtered.empty:
            filtered = city_filtered

    # ── Step 5: Sort — Public first, then by name ─
    type_order = {
        "Public": 0, "Charter": 1, "Magnet": 2,
        "Vocational": 3, "Private": 4, "Special Ed": 5
    }
    filtered["_type_order"] = filtered["type"].map(
        lambda t: type_order.get(t, 9)
    )

    # STEAM/STEM schools always float to top
    filtered["_is_steam"] = filtered["name"].str.contains(
        "STEAM|STEM", case=False, na=False
    ).astype(int).map({1: 0, 0: 1})

    filtered = (
        filtered
        .sort_values(["_is_steam", "_type_order", "name"])
        .drop(columns=["_type_order", "_is_steam"])
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
            return "" if s in ["nan", "None", "none", "NaN"] else s

        website      = clean(row.get("website",  ""))
        county_val   = clean(row.get("county",   ""))
        city_val     = clean(row.get("city",     ""))
        district_val = clean(row.get("district", ""))

        if website and not website.startswith("http"):
            website = "https://" + website

        # Use requested level for display — not NCES level
        # (STEAM schools may be classified differently)
        display_level = level

        description = _build_description(
            stype    = clean(row.get("type", "Public")),
            level    = display_level,
            city     = city_val,
            state    = state,
            county   = county_val,
            district = district_val
        )

        schools.append({
            "school_id":            clean(row.get("school_id", "")),
            "name":                  name,
            "type":                  clean(row.get("type", "Public")),
            "level":                 display_level,
            "state":                 state,
            "county":                county_val,
            "city":                  city_val.title(),
            "district":              district_val,
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
            "source":               "NCES CCD 2022-23",
        })

    return schools


def _build_description(
    stype, level, city, state,
    county="", district=""
):
    """Build clean description without double words."""
    level_map = {
        "Elementary":    "elementary",
        "Middle School": "middle",
        "High School":   "high",
        "Preschool":     "preschool",
    }
    level_word = level_map.get(level, level.lower())

    loc_parts = []
    if city and city not in ["nan", "None", ""]:
        loc_parts.append(city.title())
    if district and district not in ["nan", "None", ""]:
        loc_parts.append(district)
    elif county and county not in ["nan", "None", ""]:
        loc_parts.append(f"{county} County")
    if state:
        loc_parts.append(state)
    location = ", ".join(loc_parts) if loc_parts else state

    return f"{stype} {level_word} school in {location}."


def _tavily_k12_search(state, level, county=None, limit=10):
    """Tavily web search fallback."""
    print(f"   🌐 Web search: {level} in {state}...")

    location = (
        f"{county}, {state}"
        if county and county not in [
            "All Counties", "All Districts",
            "Select County", ""
        ]
        else state
    )
    query = (
        f"list of {level} schools in {location} "
        f"with school names and addresses"
    )

    try:
        results     = tavily.search(
            query        = query,
            max_results  = 8,
            search_depth = "advanced"
        )
        web_results = results.get("results", [])
    except Exception as e:
        print(f"   ❌ Search error: {e}")
        return []

    if not web_results:
        return []

    schools    = []
    seen_names = set()

    for result in web_results:
        content   = (
            result.get("content", "") + " " +
            result.get("title",   "")
        )
        url       = result.get("url", "")
        extracted = _extract_school_names(content, level)

        for school_info in extracted:
            name = school_info["name"]
            if name in seen_names or len(name) < 5:
                continue
            seen_names.add(name)

            description = _build_description(
                stype    = school_info.get("type", "Public"),
                level    = level,
                city     = school_info.get("city", ""),
                state    = state,
                district = county or ""
            )

            schools.append({
                "school_id":            f"TAV_{name[:12].replace(' ','_')}_{state[:2]}",
                "name":                  name,
                "type":                  school_info.get("type", "Public"),
                "level":                 level,
                "state":                 state,
                "county":                school_info.get("county", county or ""),
                "city":                  school_info.get("city", ""),
                "district":              county or "",
                "rating":                0.0,
                "tuition_min":           0,
                "tuition_max":           0,
                "student_count":         0,
                "teacher_student_ratio": "N/A",
                "ap_courses":            0,
                "clubs":                 0,
                "application_deadline":  "Contact school",
                "website":               url if "school" in url.lower() else "",
                "application_fee":       0,
                "description":           description,
                "source":               "Web Search"
            })

            if len(schools) >= limit:
                break

        if len(schools) >= limit:
            break

    if not schools:
        schools = _fallback_from_titles(
            web_results, level, state, county, limit
        )

    print(f"   ✅ Web search: {len(schools)} schools.")
    return schools


def _extract_school_names(content, level):
    """Extract school names from web content."""
    schools  = []
    lines    = content.split("\n")

    level_keywords = {
        "Elementary":    ["elementary", "elem", "primary"],
        "Middle School": ["middle", "intermediate", "junior high"],
        "High School":   ["high school", "senior high"],
        "Preschool":     ["preschool", "pre-k", "early learning"],
    }
    keywords = level_keywords.get(level, ["school"])

    skip_patterns = [
        r"^#+\s", r"^here are", r"^best\s",
        r"^top\s+\d", r"^list of", r"^the best",
        r"^\d+\s+best", r"^according", r"^schools in",
        r"^public school", r"^\*\*", r"^source:",
        r"^data from:", r"https?://", r"^ranked",
    ]
    generic_phrases = [
        "here are", "best schools", "top schools",
        "list of", "schools in", "public schools",
        "find schools", "all schools",
    ]

    for line in lines:
        line_clean = line.strip()
        if len(line_clean) < 8 or len(line_clean) > 80:
            continue
        line_lower = line_clean.lower()
        if any(re.match(p, line_lower) for p in skip_patterns):
            continue
        if not any(kw in line_lower for kw in keywords):
            continue

        name = re.sub(r"^#+\s*",           "", line_clean)
        name = re.sub(r"^\d+[\.\)\-]\s*",  "", name)
        name = re.sub(r"\s*[-–|:]\s*.*$",  "", name)
        name = re.sub(r"\*+",              "", name)
        name = re.sub(r"\s+",              " ", name).strip()
        name = name.strip("•·").strip()

        if len(name.split()) > 8 or len(name.split()) < 2:
            continue
        if any(p in name.lower() for p in generic_phrases):
            continue
        if not any(
            w[0].isupper() for w in name.split() if len(w) > 1
        ):
            continue

        stype = "Public"
        if any(w in line_lower for w in [
            "private", "academy", "montessori",
            "christian", "catholic"
        ]):
            stype = "Private"
        if "charter" in line_lower:
            stype = "Charter"

        schools.append({
            "name": name, "type": stype,
            "city": "", "county": ""
        })

    return schools


def _fallback_from_titles(
    web_results, level, state, county, limit
):
    """Last resort — build entries from search titles."""
    schools = []
    skip_phrases = [
        "here are", "best schools", "top schools",
        "list of", "schools in", "ranked",
        "overview", "guide", "wikipedia", "directory",
    ]
    level_keywords = {
        "Elementary":    ["elementary", "elem", "primary"],
        "Middle School": ["middle", "intermediate"],
        "High School":   ["high school", "senior high"],
        "Preschool":     ["preschool", "pre-k", "early"],
    }
    kws = level_keywords.get(level, ["school"])

    for r in web_results[:limit]:
        title = r.get("title", "").strip()
        url   = r.get("url",   "")
        if not title or len(title) < 5:
            continue
        if any(p in title.lower() for p in skip_phrases):
            continue
        if not any(kw in title.lower() for kw in kws):
            continue

        name = re.sub(r"\s*[-–|]\s*.*$", "", title).strip()
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) > 80 or len(name.split()) > 9 or len(name) < 5:
            continue

        schools.append({
            "school_id":            f"TAV_{name[:12].replace(' ','_')}_{state[:2]}",
            "name":                  name,
            "type":                  "Public",
            "level":                 level,
            "state":                 state,
            "county":                county or "",
            "city":                  "",
            "district":              county or "",
            "rating":                0.0,
            "tuition_min":           0,
            "tuition_max":           0,
            "student_count":         0,
            "teacher_student_ratio": "N/A",
            "ap_courses":            0,
            "clubs":                 0,
            "application_deadline":  "Contact school",
            "website":               url,
            "application_fee":       0,
            "description":           _build_description(
                "Public", level, "", state, county or ""
            ),
            "source": "Web Search"
        })

    return schools