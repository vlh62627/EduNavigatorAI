import os
import re
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

K12_DB_PATH = "data/k12_schools.csv"


def fetch_k12_schools(state, level, county=None, limit=30):
    """
    Fetch K-12 schools.
    Priority order:
        1. Local NCES CCD database (data/k12_schools.csv)
        2. Tavily web search fallback
    """
    print(f"\n🏫 K-12 Search: {level} in {state}...")

    # ── Priority 1: Local NCES Database ───────────
    if os.path.exists(K12_DB_PATH):
        local_results = _get_from_local_db(
            state, level, county, limit
        )
        if local_results:
            print(
                f"   ✅ Local DB: "
                f"{len(local_results)} schools found."
            )
            return local_results
        else:
            print(
                f"   ⚠️ Local DB has no results for "
                f"{level} in {state}. Trying web search..."
            )
    else:
        print(
            f"   ℹ️ Local K-12 DB not found. "
            f"Using web search..."
        )

    # ── Priority 2: Tavily Web Search ─────────────
    return _tavily_k12_search(state, level, county, limit)


def _get_from_local_db(state, level, county=None, limit=30):
    """
    Query the local NCES CCD CSV database.
    Returns list of school dicts or empty list.
    """
    try:
        import pandas as pd
        df = pd.read_csv(K12_DB_PATH, low_memory=False)
    except Exception as e:
        print(f"   ❌ Error reading local DB: {e}")
        return []

    # Filter by state and level
    mask = (
        (df["state"] == state) &
        (df["level"] == level)
    )
    filtered = df[mask].copy()

    if filtered.empty:
        return []

    # Apply county filter if provided
    if county and county not in [
        "All Counties", "Select County", "", "None"
    ]:
        county_clean = county.replace(" County", "").strip()
        county_mask  = filtered["county"].str.contains(
            county_clean, case=False, na=False
        )
        county_filtered = filtered[county_mask]
        # Only apply county filter if results exist
        if not county_filtered.empty:
            filtered = county_filtered

    # Sort by student count descending
    if "student_count" in filtered.columns:
        filtered = filtered.sort_values(
            "student_count", ascending=False
        )

    filtered = filtered.head(limit).reset_index(drop=True)

    # Convert to list of dicts in our schema
    schools = []
    for _, row in filtered.iterrows():
        school_id = str(row.get("school_id", ""))
        name      = str(row.get("name",      ""))
        if not name or name == "nan":
            continue

        county_val = str(row.get("county", "") or "")
        if county_val in ["nan", "None", "none"]:
            county_val = ""

        city_val = str(row.get("city", "") or "")
        if city_val in ["nan", "None", "none"]:
            city_val = ""

        website_val = str(row.get("website", "") or "")
        if website_val in ["nan", "None", "none"]:
            website_val = ""
        if website_val and not website_val.startswith("http"):
            website_val = "https://" + website_val

        district_val = str(row.get("district", "") or "")
        if district_val in ["nan", "None", "none"]:
            district_val = ""

        student_count = int(
            row.get("student_count", 0) or 0
        )

        # Build clean description
        description = _build_description(
            stype    = str(row.get("type", "Public")),
            level    = level,
            city     = city_val,
            state    = state,
            county   = county_val,
            district = district_val,
            students = student_count
        )

        schools.append({
            "school_id":            school_id,
            "name":                  name,
            "type":                  str(row.get("type", "Public")),
            "level":                 level,
            "state":                 state,
            "county":                county_val,
            "city":                  city_val,
            "district":              district_val,
            "rating":                float(row.get("rating", 0.0) or 0.0),
            "tuition_min":           0,
            "tuition_max":           0,
            "student_count":         student_count,
            "teacher_student_ratio": "N/A",
            "ap_courses":            0,
            "clubs":                 0,
            "application_deadline":  "Contact school",
            "website":               website_val,
            "application_fee":       0,
            "description":           description,
            "source":               "NCES CCD Database"
        })

    return schools


def _build_description(
    stype, level, city, state,
    county="", district="", students=0
):
    """
    Build a clean description without repeating
    words or showing internal source info.
    """
    level_map = {
        "Elementary":    "elementary",
        "Middle School": "middle",
        "High School":   "high",
        "Preschool":     "preschool",
    }
    level_word = level_map.get(level, level.lower())

    # Build location string
    loc_parts = []
    if city:
        loc_parts.append(city)
    if county and county.lower() not in ["", "nan", "none"]:
        cty = county.replace(" County", "").strip()
        if cty:
            loc_parts.append(f"{cty} County")
    if state:
        loc_parts.append(state)
    location = ", ".join(loc_parts) if loc_parts else state

    desc = f"{stype} {level_word} school in {location}."

    if district and district.lower() not in ["nan", "none", ""]:
        desc += f" Part of {district}."

    if students > 0:
        desc += f" Enrollment: {students:,} students."

    return desc


def _tavily_k12_search(state, level, county=None, limit=10):
    """
    Tavily web search fallback for K-12 schools.
    Used when local NCES database is not available
    or has no results for the given state/level.
    """
    print(f"   🌐 Web search: {level} schools in {state}...")

    location = (
        f"{county} County, {state}"
        if county and county not in [
            "All Counties", "Select County", ""
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
        print(f"   ❌ Web search error: {e}")
        return []

    if not web_results:
        print("   ⚠️ No web results found.")
        return []

    schools    = []
    seen_names = set()

    for result in web_results:
        content = (
            result.get("content", "") + " " +
            result.get("title",   "")
        )
        url = result.get("url", "")

        extracted = _extract_school_names(content, level)

        for school_info in extracted:
            name = school_info["name"]

            if name in seen_names or len(name) < 5:
                continue
            seen_names.add(name)

            city         = school_info.get("city",   "")
            county_found = school_info.get("county", county or "")

            description = _build_description(
                stype   = school_info.get("type", "Public"),
                level   = level,
                city    = city,
                state   = state,
                county  = county_found
            )

            schools.append({
                "school_id": (
                    f"TAV_{name[:12].replace(' ', '_')}"
                    f"_{state[:2]}"
                ),
                "name":                  name,
                "type":                  school_info.get("type", "Public"),
                "level":                 level,
                "state":                 state,
                "county":                county_found,
                "city":                  city,
                "district":              "",
                "rating":                0.0,
                "tuition_min":           0,
                "tuition_max":           0,
                "student_count":         0,
                "teacher_student_ratio": "N/A",
                "ap_courses":            0,
                "clubs":                 0,
                "application_deadline":  "Contact school",
                "website": (
                    url if "school" in url.lower() else ""
                ),
                "application_fee":       0,
                "description":           description,
                "source":               "Web Search"
            })

            if len(schools) >= limit:
                break

        if len(schools) >= limit:
            break

    # Fallback to titles if content parsing yielded nothing
    if not schools:
        schools = _fallback_from_titles(
            web_results, level, state, county, limit
        )

    print(f"   ✅ Web search found {len(schools)} schools.")
    return schools


def _extract_school_names(content, level):
    """
    Extract school names from web content using
    pattern matching.
    """
    schools  = []
    lines    = content.split("\n")

    level_keywords = {
        "Elementary":    [
            "elementary", "elem", "primary", "grade school"
        ],
        "Middle School": [
            "middle", "intermediate", "junior high"
        ],
        "High School":   [
            "high school", "senior high", "high sch"
        ],
        "Preschool":     [
            "preschool", "pre-k", "prekindergarten",
            "early learning", "head start"
        ],
    }
    keywords = level_keywords.get(level, ["school"])

    skip_patterns = [
        r"^#+\s",
        r"^here are",
        r"^best\s",
        r"^top\s+\d",
        r"^list of",
        r"^the best",
        r"^\d+\s+best",
        r"^according",
        r"^schools in",
        r"^public school",
        r"^\*\*",
        r"^source:",
        r"^data from:",
        r"https?://",
        r"^search result",
        r"^ranked",
        r"^rating",
        r"^\d+\.",
        r"^see also",
    ]

    generic_phrases = [
        "here are", "best schools", "top schools",
        "list of", "schools in", "public schools",
        "private schools", "high schools in",
        "elementary schools in", "middle schools in",
        "preschools in", "find schools", "search schools",
        "all schools", "local schools"
    ]

    for line in lines:
        line_clean = line.strip()

        if len(line_clean) < 8 or len(line_clean) > 80:
            continue

        line_lower = line_clean.lower()

        should_skip = any(
            re.match(pat, line_lower)
            for pat in skip_patterns
        )
        if should_skip:
            continue

        if not any(kw in line_lower for kw in keywords):
            continue

        # Clean name
        name = re.sub(r"^#+\s*",           "", line_clean)
        name = re.sub(r"^\d+[\.\)\-]\s*",  "", name)
        name = re.sub(r"\s*[-–|:]\s*.*$",  "", name)
        name = re.sub(r"\*+",              "", name)
        name = re.sub(r"\s+",              " ", name)
        name = name.strip().strip("•·").strip()

        word_count = len(name.split())
        if word_count > 8 or word_count < 2:
            continue

        if any(
            phrase in name.lower()
            for phrase in generic_phrases
        ):
            continue

        # Must have at least one proper noun
        words          = name.split()
        has_proper_noun = any(
            w[0].isupper() for w in words if len(w) > 1
        )
        if not has_proper_noun:
            continue

        # School type
        stype = "Public"
        if any(w in line_lower for w in [
            "private", "academy", "montessori",
            "christian", "catholic", "independent"
        ]):
            stype = "Private"
        if "charter" in line_lower:
            stype = "Charter"
        if "magnet" in line_lower:
            stype = "Magnet"

        schools.append({
            "name":   name,
            "type":   stype,
            "city":   "",
            "county": ""
        })

    return schools


def _fallback_from_titles(
    web_results, level, state, county, limit
):
    """
    Last resort — build school entries from
    search result titles when content parsing
    yields nothing.
    """
    schools = []

    skip_phrases = [
        "here are", "best schools", "top schools",
        "list of", "schools in", "ranked", "ranking",
        "overview", "guide to", "how to find",
        "what is", "about ", "wikipedia",
        "find schools", "search for", "directory",
        "all schools", "public schools in"
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

        title_lower = title.lower()

        if any(phrase in title_lower for phrase in skip_phrases):
            continue

        if not any(kw in title_lower for kw in kws):
            continue

        # Clean title
        name = re.sub(r"\s*[-–|]\s*.*$", "", title).strip()
        name = re.sub(r"\s+", " ", name).strip()

        if len(name) > 80 or len(name.split()) > 9:
            continue
        if len(name) < 5:
            continue

        description = _build_description(
            stype  = "Public",
            level  = level,
            city   = "",
            state  = state,
            county = county or ""
        )

        schools.append({
            "school_id": (
                f"TAV_{name[:12].replace(' ', '_')}"
                f"_{state[:2]}"
            ),
            "name":                  name,
            "type":                  "Public",
            "level":                 level,
            "state":                 state,
            "county":                county or "",
            "city":                  "",
            "district":              "",
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
            "description":           description,
            "source":               "Web Search"
        })

    return schools