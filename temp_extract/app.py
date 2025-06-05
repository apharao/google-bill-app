import streamlit as st
from datetime import datetime

# Sign ranges (approximate)
ZODIAC_SIGNS = [
    ("Capricorn", (12, 22), (1, 19)),
    ("Aquarius", (1, 20), (2, 18)),
    ("Pisces", (2, 19), (3, 20)),
    ("Aries", (3, 21), (4, 19)),
    ("Taurus", (4, 20), (5, 20)),
    ("Gemini", (5, 21), (6, 20)),
    ("Cancer", (6, 21), (7, 22)),
    ("Leo", (7, 23), (8, 22)),
    ("Virgo", (8, 23), (9, 22)),
    ("Libra", (9, 23), (10, 22)),
    ("Scorpio", (10, 23), (11, 21)),
    ("Sagittarius", (11, 22), (12, 21)),
]

ZODIAC_INFO = {
    "Aries": {
        "Element": "Fire",
        "Modality": "Cardinal",
        "Ruling Planet": "Mars",
        "Traits": "Bold, energetic, and competitive. Natural leaders who thrive on challenges."
    },
    "Taurus": {
        "Element": "Earth",
        "Modality": "Fixed",
        "Ruling Planet": "Venus",
        "Traits": "Reliable, sensual, and grounded. Lovers of beauty, comfort, and stability."
    },
    "Gemini": {
        "Element": "Air",
        "Modality": "Mutable",
        "Ruling Planet": "Mercury",
        "Traits": "Curious, witty, and adaptable. Masters of communication and duality."
    },
    "Cancer": {
        "Element": "Water",
        "Modality": "Cardinal",
        "Ruling Planet": "Moon",
        "Traits": "Nurturing, emotional, and protective. Deeply connected to home and family."
    },
    "Leo": {
        "Element": "Fire",
        "Modality": "Fixed",
        "Ruling Planet": "Sun",
        "Traits": "Charismatic, proud, and dramatic. Natural performers with big hearts."
    },
    "Virgo": {
        "Element": "Earth",
        "Modality": "Mutable",
        "Ruling Planet": "Mercury",
        "Traits": "Analytical, practical, and detail-oriented. Helpers with high standards."
    },
    "Libra": {
        "Element": "Air",
        "Modality": "Cardinal",
        "Ruling Planet": "Venus",
        "Traits": "Charming, fair, and diplomatic. Seekers of beauty, harmony, and justice."
    },
    "Scorpio": {
        "Element": "Water",
        "Modality": "Fixed",
        "Ruling Planet": "Pluto (traditionally Mars)",
        "Traits": "Intense, secretive, and transformative. Powerful emotional depth and willpower."
    },
    "Sagittarius": {
        "Element": "Fire",
        "Modality": "Mutable",
        "Ruling Planet": "Jupiter",
        "Traits": "Adventurous, optimistic, and philosophical. Freedom-lovers and truth-seekers."
    },
    "Capricorn": {
        "Element": "Earth",
        "Modality": "Cardinal",
        "Ruling Planet": "Saturn",
        "Traits": "Disciplined, ambitious, and mature. Masters of long-term planning and responsibility."
    },
    "Aquarius": {
        "Element": "Air",
        "Modality": "Fixed",
        "Ruling Planet": "Uranus (traditionally Saturn)",
        "Traits": "Innovative, rebellious, and humanitarian. Thinkers ahead of their time."
    },
    "Pisces": {
        "Element": "Water",
        "Modality": "Mutable",
        "Ruling Planet": "Neptune (traditionally Jupiter)",
        "Traits": "Empathetic, dreamy, and spiritual. Artists and healers with boundless compassion."
    },
}

def get_sign(month, day):
    for sign, start, end in ZODIAC_SIGNS:
        if (month == start[0] and day >= start[1]) or (month == end[0] and day <= end[1]):
            return sign
    return "Capricorn"  # default fallback

# Streamlit App
st.set_page_config(page_title="Zodiac Sign Reader", page_icon="🌌")
st.title("🌟 Enlightened Zodiac Profile")
st.markdown("Enter your date of birth for a detailed astrological breakdown:")

name = st.text_input("Your Name")
birth_date = st.date_input("Your Date of Birth")

if st.button("Read My Stars"):
    sign = get_sign(birth_date.month, birth_date.day)
    info = ZODIAC_INFO[sign]

    st.subheader(f"🌞 Sun Sign: {sign}")
    st.write(f"**Element:** {info['Element']}")
    st.write(f"**Modality:** {info['Modality']}")
    st.write(f"**Ruling Planet:** {info['Ruling Planet']}")
    st.write(f"**Traits:** {info['Traits']}")

    st.markdown("✨ *More features like love compatibility and numerology coming soon...*")
