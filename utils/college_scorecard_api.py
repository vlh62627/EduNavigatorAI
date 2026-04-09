import os
import requests
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from dotenv import load_dotenv
load_dotenv()

SCORECARD_API_KEY = os.getenv("COLLEGE_SCORECARD_API_KEY")
SCORECARD_BASE    = "https://api.data.gov/ed/collegescorecard/v1/schools"

# Mapping our education levels to College Scorecard degree types
LEVEL_TO_DEGREE = {
    "University":        4,   # Bachelor's and above
    "Community College": 2,   # Associate's
    "Medical School":    4,   # Graduate / professional
}

# School type filter for medical schools
MEDICAL_KEYWORDS = [
    "medicine", "medical", "health sciences",
    "pharmacy", "nursing", "dental", "osteopathic",
    "chiropractic", "optometry", "veterinary"
]


def get_state_abbreviation(state_name):
    """Convert full state name to 2-letter abbreviation."""
    states = {
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
        "South Carolina": "SC", "South Dakota": "SD",
        "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
        "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
    }
    return states.get(state_name, state_name)


def fetch_universities(state, level="University", per_page=20):
    """
    Fetch universities, community colleges, or medical schools
    from the College Scorecard API for a given state.

    Returns list of standardized school dicts.
    """
    print(f"\n🎓 College Scorecard API: Fetching {level} in {state}...")

    state_abbr = get_state_abbreviation(state)
    degree     = LEVEL_TO_DEGREE.get(level, 4)

    # Build fields to retrieve
    fields = ",".join([
        "school.name",
        "school.city",
        "school.state",
        "school.school_url",
        "school.ownership",
        "school.locale",
        "latest.cost.tuition.in_state",
        "latest.cost.tuition.out_of_state",
        "latest.student.size",
        "latest.admissions.admission_rate.overall",
        "latest.admissions.sat_scores.average.overall",
        "latest.completion.rate_suppressed.overall",
        "school.degrees_awarded.predominant",
        "school.carnegie_basic",
        "latest.programs.cip_4_digit",
        "school.zip",
    ])

    params = {
        "api_key":       SCORECARD_API_KEY,
        "school.state":  state_abbr,
        "fields":        fields,
        "per_page":      per_page,
        "_sort":         "latest.student.size:desc",
    }

    # Filter by degree level and school type
    if level == "Community College":
        params["school.degrees_awarded.predominant"] = 2
    elif level == "Medical School":
        # Get all grad schools then filter by health keywords
        params["school.degrees_awarded.predominant__range"] = "3..4"
        params["per_page"] = 100
        params["_sort"] = "school.name:asc"
    elif level == "University":
        params["school.degrees_awarded.predominant__range"] = "3..4"

    try:
        response = requests.get(
            SCORECARD_BASE, params=params, timeout=15
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"   ❌ API error: {e}")
        return []

    results  = data.get("results", [])
    schools  = []

    for r in results:
        name = r.get("school.name", "Unknown")

        # Filter medical schools
        if level == "Medical School":
            name_lower = name.lower()
            health_keywords = [
                "health", "medicine", "medical", "pharmacy",
                "nursing", "dental", "osteopathic", "physician",
                "surgery", "clinical", "hospital", "biomedical",
                "optometry", "chiropractic", "veterinary",
                "icahn", "weill", "pritzker", "feinberg",
                "perelman", "keck", "geffen", "grossman",
                "college of medicine", "school of medicine",
                "health sciences", "health professions",
                "allied health", "public health"
            ]
            if not any(kw in name_lower for kw in health_keywords):
                continue

        # Ownership type
        ownership = r.get("school.ownership", 0)
        school_type = (
            "Public"  if ownership == 1 else
            "Private" if ownership in [2, 3] else
            "Unknown"
        )

        # Tuition
        tuition_in  = r.get("latest.cost.tuition.in_state")  or 0
        tuition_out = r.get("latest.cost.tuition.out_of_state") or 0
        tuition_min = min(tuition_in, tuition_out) if tuition_in and tuition_out else max(tuition_in, tuition_out)
        tuition_max = max(tuition_in, tuition_out)

        # Admission rate
        admit_rate = r.get("latest.admissions.admission_rate.overall")
        admit_text = (
            f"{round(admit_rate * 100, 1)}% acceptance rate"
            if admit_rate else "Acceptance rate not reported"
        )

        # Student size
        student_size = r.get("latest.student.size") or 0

        # Build description
        completion = r.get("latest.completion.rate_suppressed.overall")
        completion_text = (
            f" Graduation rate: {round(completion * 100, 1)}%."
            if completion else ""
        )
        description = (
            f"{school_type} {level} in {r.get('school.city', '')}, "
            f"{state}. {admit_text}.{completion_text}"
        )

        website = r.get("school.school_url") or ""
        if website and not website.startswith("http"):
            website = "https://" + website

        school = {
            "school_id":             f"API_{state_abbr}_{name[:10].replace(' ','_')}",
            "name":                   name,
            "type":                   school_type,
            "level":                  level,
            "state":                  state,
            "county":                 "",
            "city":                   r.get("school.city", ""),
            "rating":                 round(min(9.9, 7.0 + (
                                        (1 - (admit_rate or 0.5)) * 3
                                      )), 1),
            "tuition_min":            int(tuition_min),
            "tuition_max":            int(tuition_max),
            "student_count":          int(student_size),
            "teacher_student_ratio":  "N/A",
            "ap_courses":             0,
            "clubs":                  0,
            "application_deadline":   "Check website",
            "website":                website,
            "application_fee":        0,
            "description":            description,
            "source":                 "College Scorecard API"
        }
        schools.append(school)

    print(f"   ✅ Retrieved {len(schools)} {level} institutions.")
    return schools