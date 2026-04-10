import os
import requests
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from dotenv import load_dotenv
load_dotenv()

SCORECARD_BASE = "https://api.data.gov/ed/collegescorecard/v1/schools"

STATE_ABBREVIATIONS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ",
    "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "Florida": "FL",
    "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC", "Puerto Rico": "PR",
}

# ── Metro area city groupings ──────────────────────
# Selecting a major city shows all nearby metro cities
METRO_AREAS = {
    # Texas
    "Dallas":        ["Dallas", "Richardson", "Plano", "Irving",
                      "Garland", "Mesquite", "Grand Prairie",
                      "Carrollton", "Farmers Branch", "Addison",
                      "DeSoto", "Duncanville", "Cedar Hill"],
    "Fort Worth":    ["Fort Worth", "Arlington", "Mansfield",
                      "Euless", "Bedford", "Hurst", "Keller",
                      "Grapevine", "Southlake", "Colleyville"],
    "Houston":       ["Houston", "Sugar Land", "Pearland",
                      "Pasadena", "Baytown", "Katy", "Humble",
                      "Missouri City", "League City", "Galveston"],
    "Austin":        ["Austin", "Round Rock", "Cedar Park",
                      "Georgetown", "Pflugerville", "Kyle",
                      "San Marcos", "Buda", "Leander"],
    "San Antonio":   ["San Antonio", "New Braunfels",
                      "Converse", "Universal City", "Schertz",
                      "Seguin", "Boerne"],
    # New York
    "New York":      ["New York", "Brooklyn", "Queens",
                      "Bronx", "Staten Island", "Manhattan",
                      "Flushing", "Jamaica", "Astoria"],
    "Buffalo":       ["Buffalo", "Amherst", "Cheektowaga",
                      "Tonawanda", "Niagara Falls", "Lockport"],
    # California
    "Los Angeles":   ["Los Angeles", "Pasadena", "Burbank",
                      "Glendale", "Long Beach", "Torrance",
                      "Compton", "Inglewood", "Culver City",
                      "Santa Monica", "El Monte", "West Covina"],
    "San Francisco": ["San Francisco", "Oakland", "Berkeley",
                      "San Jose", "Palo Alto", "Stanford",
                      "Fremont", "Hayward", "Sunnyvale",
                      "Santa Clara", "San Mateo", "Redwood City"],
    "San Diego":     ["San Diego", "Chula Vista", "El Cajon",
                      "Escondido", "Oceanside", "Vista"],
    # Illinois
    "Chicago":       ["Chicago", "Evanston", "Oak Park",
                      "Schaumburg", "Naperville", "Aurora",
                      "Joliet", "Cicero", "Berwyn", "Elgin"],
    # Massachusetts
    "Boston":        ["Boston", "Cambridge", "Somerville",
                      "Newton", "Brookline", "Medford",
                      "Waltham", "Quincy", "Lowell", "Worcester"],
    # Washington
    "Seattle":       ["Seattle", "Bellevue", "Redmond",
                      "Kirkland", "Tacoma", "Renton",
                      "Everett", "Bothell", "Issaquah"],
    # Georgia
    "Atlanta":       ["Atlanta", "Decatur", "Marietta",
                      "Roswell", "Sandy Springs", "Alpharetta",
                      "Kennesaw", "Smyrna", "College Park"],
    # Florida
    "Miami":         ["Miami", "Coral Gables", "Hialeah",
                      "Miami Gardens", "Homestead", "Doral",
                      "Miami Beach", "North Miami"],
    "Orlando":       ["Orlando", "Kissimmee", "Sanford",
                      "Winter Park", "Oviedo", "Deltona"],
    "Tampa":         ["Tampa", "St. Petersburg", "Clearwater",
                      "Brandon", "Largo", "Sarasota"],
    # Ohio
    "Columbus":      ["Columbus", "Dublin", "Westerville",
                      "Grove City", "Hilliard", "Gahanna"],
    "Cleveland":     ["Cleveland", "Lakewood", "Euclid",
                      "Parma", "Cleveland Heights", "Shaker Heights"],
    # Pennsylvania
    "Philadelphia":  ["Philadelphia", "Camden", "Chester",
                      "Norristown", "Upper Darby", "Drexel Hill",
                      "Bryn Mawr", "Wayne", "Villanova"],
    # Michigan
    "Detroit":       ["Detroit", "Dearborn", "Ann Arbor",
                      "Warren", "Sterling Heights", "Flint",
                      "Lansing", "East Lansing"],
    # North Carolina
    "Charlotte":     ["Charlotte", "Concord", "Gastonia",
                      "Rock Hill", "Huntersville", "Matthews"],
    "Raleigh":       ["Raleigh", "Durham", "Chapel Hill",
                      "Cary", "Morrisville", "Apex"],
    # Virginia
    "Washington DC": ["Washington", "Arlington", "Alexandria",
                      "Fairfax", "Falls Church", "McLean",
                      "Bethesda", "Silver Spring", "Rockville"],
    # Arizona
    "Phoenix":       ["Phoenix", "Tempe", "Scottsdale", "Mesa",
                      "Chandler", "Gilbert", "Glendale", "Peoria"],
    # Minnesota
    "Minneapolis":   ["Minneapolis", "St. Paul", "Bloomington",
                      "Brooklyn Park", "Plymouth", "Edina",
                      "Minnetonka", "Eden Prairie"],
    # Colorado
    "Denver":        ["Denver", "Aurora", "Lakewood",
                      "Arvada", "Westminster", "Boulder",
                      "Thornton", "Fort Collins"],
    # Missouri
    "St. Louis":     ["St. Louis", "Clayton", "University City",
                      "Florissant", "Chesterfield", "Kirkwood"],
}

# ── Medical school keywords ────────────────────────
MEDICAL_KEYWORDS = [
    "health", "medicine", "medical", "pharmacy",
    "nursing", "dental", "osteopathic", "physician",
    "surgery", "clinical", "hospital", "biomedical",
    "optometry", "chiropractic", "veterinary",
    "icahn", "weill", "pritzker", "feinberg",
    "perelman", "keck", "geffen", "grossman",
    "college of medicine", "school of medicine",
    "health sciences", "health professions",
    "allied health", "public health",
    "medical center", "health center",
    "health system", "medical school",
    "school of pharmacy", "college of pharmacy",
    "college of nursing", "school of nursing",
    "cancer center", "cancer institute",
    "anderson cancer",
    "graduate school of biomedical",
    "school of public health",
    "school of dentistry", "college of dentistry",
    "college of osteopathic",
    "school of optometry", "college of optometry",
    "graduate medical", "postgraduate medicine",
]

# ── Program category keyword mapping ──────────────
PROGRAM_CATEGORIES = {
    "Engineering":      [
        "engineering", "aerospace", "mechanical", "electrical",
        "civil", "chemical", "computer engineering", "industrial",
        "biomedical engineering", "petroleum engineering",
        "materials engineering", "nuclear engineering",
    ],
    "Computer Science": [
        "computer science", "computer and information",
        "information technology", "cybersecurity", "data science",
        "software", "artificial intelligence", "information systems",
    ],
    "Business":         [
        "business", "management", "accounting", "finance",
        "marketing", "economics", "entrepreneurship", "mba",
        "commerce", "supply chain", "human resources",
    ],
    "Medicine":         [
        "medicine", "medical", "health", "nursing", "pharmacy",
        "dentistry", "optometry", "public health", "biomedical",
        "physical therapy", "occupational therapy", "radiology",
    ],
    "Law":              [
        "law", "legal", "jurisprudence", "paralegal",
        "criminal justice", "legal studies",
    ],
    "Education":        [
        "education", "teaching", "curriculum", "pedagogy",
        "early childhood", "special education",
    ],
    "Arts & Design":    [
        "art", "design", "architecture", "fine arts",
        "graphic", "music", "theatre", "film", "media",
        "visual", "performing arts", "fashion",
    ],
    "Science":          [
        "biology", "chemistry", "physics", "mathematics",
        "statistics", "geology", "environmental science",
        "neuroscience", "biochemistry", "astronomy",
    ],
    "Social Sciences":  [
        "psychology", "sociology", "political science",
        "history", "philosophy", "anthropology",
        "international relations", "communications",
    ],
    "Agriculture":      [
        "agriculture", "agronomy", "animal science",
        "food science", "horticulture", "forestry",
        "natural resources", "veterinary",
    ],
}


def get_state_abbreviation(state_name):
    return STATE_ABBREVIATIONS.get(
        state_name, state_name[:2].upper()
    )


def _extract_programs(result, level):
    """
    Extract program categories from College Scorecard
    CIP code data. Returns sorted list of category names.
    """
    found = set()
    cip_data = result.get(
        "latest.programs.cip_4_digit.title", []
    ) or []
    if isinstance(cip_data, list):
        all_titles = " ".join(str(t).lower() for t in cip_data)
    else:
        all_titles = str(cip_data).lower()
    all_titles += " " + str(
        result.get("school.name", "")
    ).lower()

    for category, keywords in PROGRAM_CATEGORIES.items():
        if any(kw in all_titles for kw in keywords):
            found.add(category)

    carnegie = int(result.get("school.carnegie_basic", 0) or 0)
    if carnegie in [15, 16, 17]:
        found.update(["Engineering", "Science", "Business"])
    elif carnegie in [18, 19, 20]:
        found.update(["Business", "Education"])

    if level == "Medical School":
        found.add("Medicine")

    return sorted(found)


def _city_matches(city, city_filter):
    """
    Check if a school's city matches the filter.
    Expands major cities to include metro area suburbs.
    """
    if not city_filter or city_filter in ["All Cities", ""]:
        return True

    # Get metro area cities for the filter
    metro_cities = METRO_AREAS.get(city_filter, [city_filter])

    city_lower = city.lower()
    return any(
        mc.lower() in city_lower or city_lower in mc.lower()
        for mc in metro_cities
    )


def fetch_universities(
    state, level, per_page=100, city_filter=None
):
    """
    Fetch universities from College Scorecard API.
    Uses pagination to get ALL schools for a state.
    Expands city filter to include metro area suburbs.
    """
    api_key = os.getenv("COLLEGE_SCORECARD_API_KEY", "")
    if not api_key:
        print("   ⚠️ No College Scorecard API key found.")
        return []

    state_abbr = get_state_abbreviation(state)
    print(
        f"\n🎓 College Scorecard API: "
        f"Fetching {level} in {state}..."
    )
    if city_filter and city_filter not in ["All Cities", ""]:
        metro = METRO_AREAS.get(city_filter, [city_filter])
        print(f"   🏙️ Metro filter: {metro[:4]}...")

    # ── Build params ───────────────────────────────
    params = {
        "api_key":      api_key,
        "school.state": state_abbr,
        "fields": (
            "school.name,school.city,id,"
            "school.ownership,"
            "school.degrees_awarded.predominant,"
            "latest.student.size,"
            "latest.cost.tuition.in_state,"
            "latest.cost.tuition.out_of_state,"
            "latest.admissions.admission_rate.overall,"
            "school.school_url,"
            "latest.programs.cip_4_digit.title,"
            "school.carnegie_basic"
        ),
        "per_page": 100,
        "_sort":    "school.name:asc",
    }

    if level == "Community College":
        params["school.degrees_awarded.predominant"] = 2
    elif level in ["Medical School", "University"]:
        params["school.degrees_awarded.predominant__range"] = "3..4"

    # ── Fetch with pagination ──────────────────────
    all_results = []
    page        = 0

    while True:
        params["_page"] = page
        try:
            resp = requests.get(
                SCORECARD_BASE,
                params  = params,
                timeout = 15
            )
            resp.raise_for_status()
            data    = resp.json()
            results = data.get("results", [])
            total   = data.get("metadata", {}).get("total", 0)

            if not results:
                break

            all_results.extend(results)
            fetched = (page + 1) * 100

            print(
                f"   📄 Page {page+1}: "
                f"{len(results)} schools (total: {total})"
            )

            if fetched >= total or len(results) < 100:
                break
            if len(all_results) >= 300:
                print("   ℹ️ Capped at 300 schools.")
                break

            page += 1

        except Exception as e:
            print(f"   ❌ API error (page {page}): {e}")
            break

    # ── Filter and convert ─────────────────────────
    schools = []
    for r in all_results:
        name = str(r.get("school.name", "") or "").strip()
        if not name:
            continue

        # Medical school keyword filter
        if level == "Medical School":
            if not any(
                kw in name.lower() for kw in MEDICAL_KEYWORDS
            ):
                continue

        city = str(r.get("school.city", "") or "").strip()

        # Metro-aware city filter
        if not _city_matches(city, city_filter):
            continue

        owner    = int(r.get("school.ownership",  1) or 1)
        size     = int(r.get("latest.student.size", 0) or 0)
        url      = str(r.get("school.school_url",  "") or "")
        adm_rate = r.get(
            "latest.admissions.admission_rate.overall"
        )
        t_in  = r.get("latest.cost.tuition.in_state",     0) or 0
        t_out = r.get("latest.cost.tuition.out_of_state",  0) or 0
        if t_in == 0 and t_out == 0:
            t_in  = 10000 if owner == 1 else 35000
            t_out = 25000 if owner == 1 else 35000

        stype = {
            1: "Public", 2: "Private", 3: "Private"
        }.get(owner, "Public")

        if url and not url.startswith("http"):
            url = "https://" + url

        acc = (
            f"{int(float(adm_rate)*100)}% acceptance rate"
            if adm_rate is not None
            else "Contact school for admission info"
        )
        description = (
            f"{stype} {level.lower()} in {city}, {state}. "
            f"{acc}. Enrollment: {size:,} students."
            if size > 0
            else f"{stype} {level.lower()} in {city}, {state}. {acc}."
        )

        programs  = _extract_programs(r, level)
        school_id = (
            f"CS_{r.get('id', name[:8].replace(' ','_'))}"
        )

        schools.append({
            "school_id":            school_id,
            "name":                  name,
            "type":                  stype,
            "level":                 level,
            "state":                 state,
            "county":                "",
            "city":                  city,
            "district":              "",
            "rating":                0.0,
            "tuition_min":           int(t_in),
            "tuition_max":           int(t_out),
            "student_count":         size,
            "teacher_student_ratio": "N/A",
            "ap_courses":            0,
            "clubs":                 0,
            "application_deadline":  "Contact school",
            "website":               url,
            "application_fee":       0,
            "description":           description,
            "programs":              programs,
            "source":               "College Scorecard API",
        })

    # Sort: Public first, then Private, then by name
    type_order = {"Public": 0, "Private": 1}
    schools    = sorted(
        schools,
        key=lambda s: (
            type_order.get(s.get("type", "Private"), 2),
            s.get("name", "")
        )
    )

    print(
        f"   ✅ Retrieved {len(schools)} "
        f"{level} institutions."
    )
    return schools