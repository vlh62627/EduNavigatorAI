import pandas as pd

df = pd.read_csv("data/k12_schools.csv", low_memory=False)

# Remove existing manual entries to avoid duplicates
manual_ids = [
    "ALLEN_STEAM_001", "FRISCO_STEAM_001",
    "PLANO_STEAM_001", "MCKINNEY_STEAM_001",
    "LEWISVILLE_STEAM_001"
]
df = df[~df["school_id"].isin(manual_ids)]

steam_facilities = [
    {
        "school_id": "ALLEN_STEAM_001",
        "name": "ALLEN ISD STEAM CENTER",
        "type": "Public", "level": "Elementary",
        "state": "Texas", "county": "Collin",
        "city": "ALLEN", "district": "ALLEN ISD",
        "zip": "75013", "rating": 0.0,
        "tuition_min": 0, "tuition_max": 0,
        "student_count": 0,
        "teacher_student_ratio": "N/A",
        "ap_courses": 0, "clubs": 0,
        "application_deadline": "Contact school",
        "website": "https://www.allenisd.org/steam",
        "application_fee": 0,
        "description": "Public STEAM facility in Allen, Allen ISD, Texas. State-of-the-art 111,000 sq ft center for Science, Technology, Engineering, Arts and Mathematics. Address: 1680 Ridgeview Drive, Allen TX 75013. Phone: 469-675-2700.",
    },
    {
        "school_id": "MCKINNEY_STEAM_001",
        "name": "MCKINNEY ISD STEAM CENTER",
        "type": "Public", "level": "Elementary",
        "state": "Texas", "county": "Collin",
        "city": "MCKINNEY", "district": "MCKINNEY ISD",
        "zip": "75069", "rating": 0.0,
        "tuition_min": 0, "tuition_max": 0,
        "student_count": 0,
        "teacher_student_ratio": "N/A",
        "ap_courses": 0, "clubs": 0,
        "application_deadline": "Contact school",
        "website": "https://www.mckinneyisd.net",
        "application_fee": 0,
        "description": "Public STEAM facility in McKinney, McKinney ISD, Texas. Specialized center for Science, Technology, Engineering, Arts and Mathematics education.",
    },
    {
        "school_id": "PLANO_STEAM_001",
        "name": "PLANO ISD STEAM CENTER",
        "type": "Public", "level": "Elementary",
        "state": "Texas", "county": "Collin",
        "city": "PLANO", "district": "PLANO ISD",
        "zip": "75025", "rating": 0.0,
        "tuition_min": 0, "tuition_max": 0,
        "student_count": 0,
        "teacher_student_ratio": "N/A",
        "ap_courses": 0, "clubs": 0,
        "application_deadline": "Contact school",
        "website": "https://www.pisd.edu",
        "application_fee": 0,
        "description": "Public STEAM facility in Plano, Plano ISD, Texas. Specialized center for Science, Technology, Engineering, Arts and Mathematics education.",
    },
    {
        "school_id": "FRISCO_STEAM_001",
        "name": "FRISCO ISD STEAM CENTER",
        "type": "Public", "level": "Elementary",
        "state": "Texas", "county": "Collin",
        "city": "FRISCO", "district": "FRISCO ISD",
        "zip": "75035", "rating": 0.0,
        "tuition_min": 0, "tuition_max": 0,
        "student_count": 0,
        "teacher_student_ratio": "N/A",
        "ap_courses": 0, "clubs": 0,
        "application_deadline": "Contact school",
        "website": "https://www.friscoisd.org",
        "application_fee": 0,
        "description": "Public STEAM facility in Frisco, Frisco ISD, Texas. Specialized center for Science, Technology, Engineering, Arts and Mathematics education.",
    },
    {
        "school_id": "LEWISVILLE_STEAM_001",
        "name": "LEWISVILLE ISD STEM CENTER",
        "type": "Public", "level": "Elementary",
        "state": "Texas", "county": "Denton",
        "city": "LEWISVILLE", "district": "LEWISVILLE ISD",
        "zip": "75067", "rating": 0.0,
        "tuition_min": 0, "tuition_max": 0,
        "student_count": 0,
        "teacher_student_ratio": "N/A",
        "ap_courses": 0, "clubs": 0,
        "application_deadline": "Contact school",
        "website": "https://www.lisd.net",
        "application_fee": 0,
        "description": "Public STEM facility in Lewisville, Lewisville ISD, Texas. Specialized center for Science, Technology, Engineering and Mathematics education.",
    },
]

new_rows = pd.DataFrame(steam_facilities)
df = pd.concat([df, new_rows], ignore_index=True)
df.to_csv("data/k12_schools.csv", index=False)

print(f"✅ Added {len(steam_facilities)} STEAM facilities.")
print(f"   Total schools: {len(df):,}")