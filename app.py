import os
import re
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

import streamlit as st
from dotenv import load_dotenv
from utils.geo_filter import (
    load_geo_data,
    get_all_states,
    get_education_levels,
    is_county_applicable,
    get_counties_for_level,
    get_cities_for_county,
    get_cities_for_university,
    filter_schools,
    get_filter_summary,
    has_local_data
)
from utils.embeddings    import load_vector_db
from agents.orchestrator import orchestrator
from utils.startup       import ensure_data_files

load_dotenv(override=True)

# ── Page Configuration ─────────────────────────────
st.set_page_config(
    page_title="EduNavigator AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b3a5c 50%, #1e5f8e 100%);
        padding: 1.2rem 2rem;
        border-radius: 14px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: "";
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background:
            radial-gradient(circle at 30% 50%, rgba(212,175,55,0.08) 0%, transparent 60%),
            radial-gradient(circle at 70% 50%, rgba(255,255,255,0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .main-header h1 {
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem;
        margin: 0 0 0.2rem;
        font-weight: 700;
        letter-spacing: -0.3px;
        position: relative;
        color: #ffffff !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .main-header .gold-line {
        width: 40px; height: 2px;
        background: linear-gradient(90deg, #d4af37, #f5d060);
        margin: 0.4rem auto;
        border-radius: 2px;
    }
    .main-header p {
        font-size: 0.85rem;
        margin: 0;
        opacity: 0.8;
        font-weight: 300;
        letter-spacing: 0.5px;
        position: relative;
        color: #ffffff;
    }
    .school-card {
        background: #ffffff;
        border: 1px solid #e8edf2;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(13,27,42,0.06);
        transition: all 0.25s ease;
        border-left: 4px solid #1b3a5c;
    }
    .school-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(13,27,42,0.12);
        border-left-color: #d4af37;
    }
    .school-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #0d1b2a;
        margin-bottom: 0.3rem;
    }
    .school-meta {
        font-size: 0.82rem;
        color: #7a8a99;
        margin-bottom: 0.6rem;
    }
    .school-desc {
        font-size: 0.9rem;
        color: #3d5166;
        margin-bottom: 0.9rem;
        line-height: 1.6;
        font-weight: 300;
    }
    .chip {
        display: inline-block;
        background: #f0f5ff;
        color: #1b3a5c;
        border-radius: 20px;
        padding: 3px 11px;
        font-size: 0.76rem;
        margin: 2px 3px 2px 0;
        font-weight: 500;
        border: 1px solid #dce8f5;
    }
    .program-chip {
        display: inline-block;
        background: #f0f4f8;
        color: #2c3e50;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.74rem;
        margin: 2px 3px 2px 0;
        font-weight: 500;
        border: 1px solid #d0dce8;
    }
    .programs-label {
        font-size: 0.72rem;
        color: #7a8a99;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 4px;
    }
    .filter-banner {
        background: linear-gradient(90deg, #e8f0fa, #f5f8ff);
        border-left: 4px solid #1b3a5c;
        padding: 0.7rem 1.2rem;
        border-radius: 0 10px 10px 0;
        color: #1b3a5c;
        font-size: 0.9rem;
        margin-bottom: 1.4rem;
        font-weight: 500;
    }
    .sidebar-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #0d1b2a;
        margin-bottom: 1rem;
    }
    .sidebar-step {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #7a8a99;
        margin-bottom: 0.3rem;
        margin-top: 0.8rem;
    }
    .welcome-card {
        background: linear-gradient(135deg, #f8faff, #eef3fb);
        border: 1px solid #dce8f5;
        border-radius: 12px;
        padding: 1.4rem;
        text-align: center;
    }
    .welcome-card .step-num {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #d4af37;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    .welcome-card .step-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0d1b2a;
        margin-bottom: 0.4rem;
    }
    .welcome-card .step-desc {
        font-size: 0.8rem;
        color: #7a8a99;
        font-weight: 300;
        line-height: 1.5;
    }
    .agent-card {
        background: white;
        border: 1px solid #e8edf2;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        transition: transform 0.2s;
    }
    .agent-card:hover { transform: translateY(-2px); }
    .agent-icon  { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .agent-name  { font-weight: 600; color: #0d1b2a; font-size: 0.9rem; margin-bottom: 0.3rem; }
    .agent-desc  { font-size: 0.78rem; color: #7a8a99; line-height: 1.5; font-weight: 300; }
    .stat-bar    { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
    .stat-item   {
        flex: 1;
        background: linear-gradient(135deg, #0d1b2a, #1b3a5c);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .stat-value  {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #d4af37;
    }
    .stat-label  {
        font-size: 0.72rem;
        color: rgba(255,255,255,0.7);
        margin-top: 2px;
        font-weight: 300;
    }
    .edu-footer  {
        text-align: center;
        padding: 1.5rem 0 0.5rem;
        color: #b0bec5;
        font-size: 0.76rem;
        border-top: 1px solid #e8edf2;
        margin-top: 2.5rem;
        font-weight: 300;
    }
    .no-results  { text-align: center; padding: 4rem 2rem; color: #b0bec5; }
    .no-results .icon { font-size: 3rem; margin-bottom: 1rem; }
    .no-results .msg  { font-size: 1rem; }
    .no-results .sub  { font-size: 0.85rem; margin-top: 0.5rem; font-weight: 300; }

    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #0d1b2a, #1b3a5c) !important;
        color: #ffffff !important;
        border: 1px solid rgba(212,175,55,0.3) !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1b3a5c, #1e5f8e) !important;
        color: #f5d060 !important;
        border-color: rgba(212,175,55,0.6) !important;
        box-shadow: 0 4px 12px rgba(13,27,42,0.3) !important;
    }
    div[data-testid="stButton"] button[kind="primary"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] {
        border-radius: 10px !important;
        border: 1px solid #e8edf2 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Load Resources Once ────────────────────────────
@st.cache_resource(show_spinner=False)
def get_resources():
    load_dotenv(override=True)
    ensure_data_files()
    df         = load_geo_data()
    collection = load_vector_db()
    return df, collection




# ── Program icons map ──────────────────────────────
PROGRAM_ICONS = {
    "Engineering":      "⚙️",
    "Computer Science": "💻",
    "Business":         "📊",
    "Medicine":         "🏥",
    "Law":              "⚖️",
    "Education":        "📚",
    "Arts & Design":    "🎨",
    "Science":          "🔬",
    "Social Sciences":  "🌍",
    "Agriculture":      "🌾",
}

# ── Rating Badge ───────────────────────────────────
def rating_badge(rating):
    r = float(rating)
    if r >= 9.0:
        color, bg, label = "#1a6b3a", "#f0faf4", "Excellent"
    elif r >= 8.0:
        color, bg, label = "#8a6a00", "#fffbef", "Good"
    else:
        color, bg, label = "#a02020", "#fff0f0", "Average"
    return (
        f'<span style="display:inline-block;background:{bg};'
        f'color:{color};border-radius:20px;padding:3px 12px;'
        f'font-size:0.78rem;font-weight:600;">'
        f'⭐ {label} {r}/10</span>'
    )


# ── CSV School Card ────────────────────────────────
def render_school_card(row, match_score=None):
    tuition = (
        "Free (Public)"
        if int(row["tuition_min"]) == 0
        else f"${int(row['tuition_min']):,} – ${int(row['tuition_max']):,}/yr"
    )
    app_fee  = int(row.get("application_fee", 0))
    fee_chip = (
        '<span class="chip">📋 No App Fee</span>'
        if app_fee == 0
        else f'<span class="chip">📋 App Fee: ${app_fee}</span>'
    )
    ap_chip = (
        f'<span class="chip">📚 {int(row["ap_courses"])} AP Courses</span>'
        if int(row["ap_courses"]) > 0 else ""
    )
    match_html = (
        f'<span class="chip" style="background:#f0faf4;'
        f'color:#1a6b3a;border:1px solid #b8e8ca;">'
        f'🎯 {match_score}% match</span>'
        if match_score else ""
    )
    city   = str(row.get("city",   "") or "").strip()
    county = str(row.get("county", "") or "").strip()
    state  = str(row.get("state",  "") or "").strip()
    lp = []
    if city:   lp.append(city)
    if county and county.lower() not in ["", "nan", "none"]:
        lp.append(f"{county} County")
    if state:  lp.append(state)
    location_str = ", ".join(lp) if lp else state

    card = (
        '<div class="school-card">'
        '<div class="school-name">🏫 ' + str(row["name"]) + '</div>'
        '<div class="school-meta">📍 ' + location_str
            + ' &nbsp;|&nbsp; 🏷️ '
            + str(row["type"]) + ' ' + str(row["level"]) + '</div>'
        '<div class="school-desc">' + str(row["description"]) + '</div>'
        + rating_badge(row["rating"]) + '&nbsp;'
        + match_html + '&nbsp;'
        + '<span class="chip">💰 ' + tuition + '</span>'
        + fee_chip
        + '<span class="chip">👥 ' + f'{int(row["student_count"]):,}' + ' students</span>'
        + '<span class="chip">👩‍🏫 ' + str(row["teacher_student_ratio"]) + '</span>'
        + '<span class="chip">🎭 ' + str(int(row["clubs"])) + ' clubs</span>'
        + ap_chip
        + '<div style="margin-top:0.9rem;padding-top:0.8rem;'
            'border-top:1px solid #f0f4f8;font-size:0.78rem;color:#9aabb8;">'
            '🗓️ Deadline: ' + str(row["application_deadline"])
            + ' &nbsp;|&nbsp; 🌐 ' + str(row["website"])
        + '</div></div>'
    )
    st.markdown(card, unsafe_allow_html=True)


# ── API School Card ────────────────────────────────
def render_api_school_card(school):
    tuition = (
        "Free / Public"
        if int(school.get("tuition_min", 0)) == 0
        else f"${int(school['tuition_min']):,} – ${int(school['tuition_max']):,}/yr"
    )
    student_count = int(school.get("student_count", 0))
    students_text = (
        f"{student_count:,} students"
        if student_count > 0 else "Enrollment not reported"
    )
    city    = str(school.get("city",   "") or "").strip()
    county  = str(school.get("county", "") or "").strip()
    state_v = str(school.get("state",  "") or "").strip()
    lp = []
    if city: lp.append(city)
    if county and county.lower() not in ["", "nan", "none"]:
        cty = county.replace(" County", "").strip()
        if cty: lp.append(f"{cty} County")
    if state_v: lp.append(state_v)
    location_str = ", ".join(lp) if lp else state_v

    school_type  = str(school.get("type",  "Public"))
    school_level = str(school.get("level", ""))

    raw_desc   = str(school.get("description", ""))
    clean_desc = re.sub(
        r'\b(\w[\w\s]*[Ss]chool)\s+school\b', r'\1', raw_desc
    )
    clean_desc = re.sub(
        r'(Source|Data from):.*$', '', clean_desc
    ).strip()

    website = str(school.get("website", "") or "")
    if website and not website.startswith("http"):
        website = "https://" + website
    website_html = (
        f'<a href="{website}" target="_blank" '
        f'style="color:#1b3a5c;">{website[:45]}</a>'
        if website else "Contact school"
    )
    app_fee  = int(school.get("application_fee", 0))
    fee_chip = (
        '<span class="chip">📋 No App Fee</span>'
        if app_fee == 0
        else f'<span class="chip">📋 App Fee: ${app_fee}</span>'
    )
    rating      = float(school.get("rating", 0.0))
    rating_html = rating_badge(rating) + "&nbsp;" if rating > 0 else ""
    district    = str(school.get("district", "") or "").strip()
    district_html = (
        f'<span class="chip">🏛️ {district[:40]}</span>'
        if district and district not in ["nan", "None", ""] else ""
    )

    # ── Programs offered ───────────────────────────
    programs     = school.get("programs", []) or []
    program_html = ""
    if programs:
        chips = "".join([
            f'<span class="program-chip">{PROGRAM_ICONS.get(p, "📖")} {p}</span>'
            for p in programs[:7]
        ])
        program_html = (
            '<div style="margin-top:0.6rem;">'
            '<span class="programs-label">Programs:</span>'
            + chips +
            '</div>'
        )

    card = (
        '<div class="school-card">'
        '<div class="school-name">🏫 ' + str(school["name"]) + '</div>'
        '<div class="school-meta">📍 ' + location_str
            + ' &nbsp;|&nbsp; 🏷️ '
            + school_type + ' ' + school_level + '</div>'
        '<div class="school-desc">' + clean_desc + '</div>'
        + program_html
        + '<div style="margin-top:0.8rem;">'
        + rating_html
        + '<span class="chip">💰 ' + tuition + '</span>'
        + fee_chip
        + '<span class="chip">👥 ' + students_text + '</span>'
        + district_html
        + '</div>'
        + '<div style="margin-top:0.9rem;padding-top:0.8rem;'
            'border-top:1px solid #f0f4f8;font-size:0.78rem;color:#9aabb8;">'
            '🗓️ Deadline: '
            + str(school.get("application_deadline", "Contact school"))
            + ' &nbsp;|&nbsp; 🌐 ' + website_html
        + '</div></div>'
    )
    st.markdown(card, unsafe_allow_html=True)


# ── Main App ───────────────────────────────────────
def main():

    st.markdown("""
    <div class="main-header">
        <h1>🎓 EduNavigator AI</h1>
        <div class="gold-line"></div>
        <p>Intelligent School & University Discovery</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Initializing..."):
        df, collection = get_resources()

    # ══════════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════════
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">🎓 EduNavigator AI</div>',
            unsafe_allow_html=True
        )

        # Step 1: Level
        st.markdown(
            '<div class="sidebar-step">Step 1 — Education Level</div>',
            unsafe_allow_html=True
        )
        level_options  = ["Select Level"] + get_education_levels()
        selected_level = st.selectbox(
            "Level", options=level_options,
            label_visibility="collapsed"
        )

        # Step 2: State
        st.markdown(
            '<div class="sidebar-step">Step 2 — State</div>',
            unsafe_allow_html=True
        )
        state_options  = ["Select State"] + get_all_states()
        selected_state = st.selectbox(
            "State", options=state_options,
            label_visibility="collapsed"
        )

        # ── Step 3 & 4: Filters ────────────────────
        selected_county = None
        selected_city   = None

        UNI_LEVELS = ["University", "Community College", "Medical School"]
        K12_LEVELS = ["Preschool", "Elementary", "Middle School", "High School"]

        if selected_level in K12_LEVELS:
            # ── K-12: District + City ──────────────
            st.markdown(
                '<div class="sidebar-step">Step 3 — County / District</div>',
                unsafe_allow_html=True
            )
            counties = get_counties_for_level(
                df, selected_state, selected_level
            ) or []

            if counties:
                selected_county = st.selectbox(
                    "County / District",
                    options=["All Districts"] + counties,
                    label_visibility="collapsed"
                )
            else:
                st.caption(
                    f"All districts in {selected_state}"
                    if selected_state != "Select State"
                    else "Select a state first"
                )

            st.markdown(
                '<div class="sidebar-step">Step 4 — City (Optional)</div>',
                unsafe_allow_html=True
            )
            cities = get_cities_for_county(
                selected_state,
                selected_level,
                selected_county
            ) if selected_state != "Select State" else []

            if cities:
                selected_city = st.selectbox(
                    "City",
                    options=["All Cities"] + cities,
                    label_visibility="collapsed"
                )
            else:
                st.caption("Select a district to filter by city")

        elif selected_level in UNI_LEVELS:
            # ── University: City only ──────────────
            st.markdown(
                '<div class="sidebar-step">Step 3 — City (Optional)</div>',
                unsafe_allow_html=True
            )
            if selected_state != "Select State":
                with st.spinner("Loading cities..."):
                    uni_cities = get_cities_for_university(
                        selected_state, selected_level
                    ) or []
            else:
                uni_cities = []

            if uni_cities:
                selected_city = st.selectbox(
                    "City",
                    options=["All Cities"] + uni_cities,
                    label_visibility="collapsed"
                )
            else:
                st.caption(
                    f"All cities in {selected_state}"
                    if selected_state != "Select State"
                    else "Select a state first"
                )

        elif selected_level != "Select Level":
            st.markdown(
                '<div class="sidebar-step">Step 3 — County / District</div>',
                unsafe_allow_html=True
            )
            st.caption("Select a level first")

        st.divider()

        # Search Query
        st.markdown(
            '<div class="sidebar-step">Search Query (Optional)</div>',
            unsafe_allow_html=True
        )
        search_query = st.text_area(
            "Query",
            placeholder=(
                "e.g. best STEM programs\n"
                "e.g. schools with scholarships\n"
                "e.g. small class sizes"
            ),
            height=100,
            label_visibility="collapsed",
            key="search_query_input"
        )

        st.divider()

        search_clicked = st.button(
            "🔍  Search",
            use_container_width=True,
            type="primary",
            disabled=(
                selected_level == "Select Level" or
                selected_state == "Select State"
            )
        )

        st.divider()

        # PDF Checklist
        st.markdown(
            '<div class="sidebar-step">PDF Checklist</div>',
            unsafe_allow_html=True
        )
        generate_pdf = st.toggle(
            "Generate application checklist PDF",
            value=False
        )
        pdf_school = None
        if generate_pdf:
            pdf_school = st.text_input(
                "School name",
                placeholder="e.g. University of Alaska Anchorage"
            )

    # ══════════════════════════════════════════════
    # MAIN CONTENT
    # ══════════════════════════════════════════════
    filters_ready = (
        selected_level != "Select Level" and
        selected_state != "Select State"
    )

    if not filters_ready:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="welcome-card">
                <div class="step-num">01</div>
                <div class="step-title">Education Level</div>
                <div class="step-desc">Choose from Preschool
                through Medical School</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="welcome-card">
                <div class="step-num">02</div>
                <div class="step-title">Select State</div>
                <div class="step-desc">All 50 US states
                covered with live data</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="welcome-card">
                <div class="step-num">03</div>
                <div class="step-title">Search</div>
                <div class="step-desc">AI finds the best
                matches instantly</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="stat-bar">
            <div class="stat-item">
                <div class="stat-value">100K+</div>
                <div class="stat-label">Schools Available</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">50</div>
                <div class="stat-label">States Covered</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">7</div>
                <div class="stat-label">Education Levels</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">3</div>
                <div class="stat-label">Live Data Sources</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### How It Works")
        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown("""
            <div class="agent-card">
                <div class="agent-icon">📚</div>
                <div class="agent-name">Librarian Agent</div>
                <div class="agent-desc">Searches local vector
                database for fast semantic
                matching on known schools</div>
            </div>""", unsafe_allow_html=True)
        with a2:
            st.markdown("""
            <div class="agent-card">
                <div class="agent-icon">🔍</div>
                <div class="agent-name">Researcher Agent</div>
                <div class="agent-desc">Searches live web for
                any school anywhere in
                real time</div>
            </div>""", unsafe_allow_html=True)
        with a3:
            st.markdown("""
            <div class="agent-card">
                <div class="agent-icon">📄</div>
                <div class="agent-name">Doc Specialist</div>
                <div class="agent-desc">Generates personalized
                PDF application checklists
                with pro tips</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="edu-footer">
            EduNavigator AI &nbsp;·&nbsp;
            Powered by Groq LLaMA 3.3 &nbsp;·&nbsp;
            ChromaDB &nbsp;·&nbsp; NCES CCD &nbsp;·&nbsp;
            College Scorecard API
        </div>
        """, unsafe_allow_html=True)

    elif not search_clicked:
        summary = get_filter_summary(
            selected_state, selected_level,
            selected_county, selected_city
        )
        st.markdown(
            f'<div class="filter-banner">📍 {summary}</div>',
            unsafe_allow_html=True
        )
        city_label = (
            f" · {selected_city}"
            if selected_city and
            selected_city != "All Cities" else ""
        )
        county_label = (
            f" · {selected_county}"
            if selected_county and
            selected_county not in [
                "All Counties", "All Districts"
            ] else ""
        )
        st.info(
            f"✅ Filters ready: **{selected_level}** in "
            f"**{selected_state}**{county_label}{city_label}\n\n"
            f"Click **🔍 Search** to find schools."
        )

    else:
        # ══════════════════════════════════════════
        # RESULTS
        # ══════════════════════════════════════════
        summary = get_filter_summary(
            selected_state, selected_level,
            selected_county, selected_city
        )
        st.markdown(
            f'<div class="filter-banner">📍 {summary}</div>',
            unsafe_allow_html=True
        )

        city_context = (
            f" in {selected_city}"
            if selected_city and
            selected_city != "All Cities" else ""
        )
        display_query = (
            search_query.strip()
            if search_query.strip()
            else (
                f"Provide {selected_level} data "
                f"in {selected_state}{city_context}"
            )
        )

        city_label = (
            f" · {selected_city}"
            if selected_city and
            selected_city != "All Cities" else ""
        )
        st.markdown(
            f"### 🏫 {selected_level} schools "
            f"in {selected_state}{city_label}"
        )

        with st.spinner("🔍 Finding schools..."):
            result = orchestrator(
                collection   = collection,
                query        = display_query,
                state        = selected_state,
                level        = selected_level,
                county       = selected_county,
                city         = (
                    selected_city
                    if selected_city and
                    selected_city != "All Cities"
                    else None
                ),
                n_results    = 20,
                generate_pdf = generate_pdf and bool(pdf_school),
                school_name  = pdf_school,
                df           = df
            )

        # ── Local / Cached Results ─────────────────
        if result["schools"] and result["local_summary"]:
            with st.expander("📝 AI Analysis", expanded=True):
                st.markdown(result["local_summary"])
            st.markdown("#### Schools")
            filtered_df = filter_schools(
                df,
                state  = selected_state,
                level  = selected_level,
                county = selected_county,
                city   = selected_city
            )
            for school_meta in result["schools"]:
                match_row = filtered_df[
                    filtered_df["name"] == school_meta["name"]
                ]
                if not match_row.empty:
                    render_school_card(match_row.iloc[0])

        # ── API Results ────────────────────────────
        if result.get("api_schools"):
            api_schools = result["api_schools"]
            c1, c2, c3  = st.columns(3)
            c1.metric("Found",   len(api_schools))
            c2.metric("Public",  len([
                s for s in api_schools
                if s.get("type") == "Public"
            ]))
            c3.metric("Private", len([
                s for s in api_schools
                if s.get("type") == "Private"
            ]))
            st.markdown("---")
            for school in api_schools:
                render_api_school_card(school)

        # ── Web Research ───────────────────────────
        if result["web_summary"] and search_query.strip():
            st.markdown("---")
            with st.expander(
                "🌐 Additional Research", expanded=True
            ):
                st.markdown(result["web_summary"])
            if result["web_sources"]:
                st.markdown("**Sources:**")
                for src in result["web_sources"]:
                    st.markdown(
                        f"- [{src['title'][:70]}]({src['url']})"
                    )

        # ── PDF Download ───────────────────────────
        if (
            result["pdf_result"] and
            result["pdf_result"]["filepath"]
        ):
            st.markdown("---")
            st.markdown("### 📄 Application Checklist")
            pdf_path = result["pdf_result"]["filepath"]
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                total = sum(
                    len(v) for v in
                    result["pdf_result"]["checklist"].values()
                )
                st.success(
                    f"✅ PDF checklist for "
                    f"**{result['pdf_result']['school_name']}**"
                    f" — {total} items"
                )
            with col_btn:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True
                    )
            with st.expander(
                "👀 Preview Checklist", expanded=False
            ):
                for section, items in (
                    result["pdf_result"]["checklist"].items()
                ):
                    if items:
                        st.markdown(f"**{section}**")
                        for item in items:
                            st.markdown(f"- ☐ {item}")

        # ── No Results ─────────────────────────────
        if (
            not result["schools"] and
            not result.get("api_schools") and
            not result["web_summary"]
        ):
            st.markdown("""
            <div class="no-results">
                <div class="icon">🔍</div>
                <div class="msg">No results found</div>
                <div class="sub">Try a different state or
                add a specific school name in the search box</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="edu-footer">
            EduNavigator AI &nbsp;·&nbsp;
            Powered by Groq LLaMA 3.3 &nbsp;·&nbsp;
            ChromaDB &nbsp;·&nbsp; NCES CCD &nbsp;·&nbsp;
            College Scorecard API
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()