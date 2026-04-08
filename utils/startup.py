import os
import requests
import pandas as pd
import streamlit as st


def ensure_data_files():
    """
    Ensure all required data files exist.
    Downloads missing files on first run.
    Called once at app startup.
    """

    # ── schools.csv — always included in repo ─────
    if not os.path.exists("data/schools.csv"):
        os.makedirs("data", exist_ok=True)

    # ── zip_county.csv — download if missing ──────
    if not os.path.exists("data/zip_county.csv"):
        _download_zip_county()

    # ── k12_schools.csv — build if missing ────────
    if not os.path.exists("data/k12_schools.csv"):
        st.warning(
            "⚠️ K-12 database not found. "
            "The app will use web search for K-12 schools. "
            "For full functionality, run "
            "`python utils/build_k12_database.py` locally "
            "and commit `data/k12_schools.csv`."
        )

    # ── outputs/ folder ───────────────────────────
    os.makedirs("outputs",  exist_ok=True)
    os.makedirs("data",     exist_ok=True)
    os.makedirs("chroma_db",exist_ok=True)


def _download_zip_county():
    """Download ZIP to county mapping."""
    print("📥 Downloading ZIP county map...")
    try:
        url  = (
            "https://raw.githubusercontent.com/"
            "scpike/us-state-county-zip/master/geo-data.csv"
        )
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            from io import StringIO
            zip_df = pd.read_csv(StringIO(resp.text))
            zip_df.columns = [c.lower() for c in zip_df.columns]
            zip_col    = next(
                (c for c in zip_df.columns if "zip"    in c), None
            )
            county_col = next(
                (c for c in zip_df.columns if "county" in c), None
            )
            if zip_col and county_col:
                result = zip_df[[zip_col, county_col]].copy()
                result.columns = ["zip", "county"]
                result["zip"]  = (
                    result["zip"].astype(str).str.zfill(5)
                )
                result = result.drop_duplicates("zip")
                os.makedirs("data", exist_ok=True)
                result.to_csv("data/zip_county.csv", index=False)
                print(f"   ✅ ZIP map: {len(result):,} ZIPs")
    except Exception as e:
        print(f"   ⚠️ ZIP download failed: {e}")