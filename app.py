import streamlit as st

# Astrological profile database (very basic for now)
astro_profiles = {
    "Aries": "Energetic, adventurous, and passionate. Natural leaders with a bold spirit.",
    "Taurus": "Reliable, patient, and grounded. Loves beauty and comfort.",
    "Gemini": "Curious, witty, and communicative. Adaptable and expressive.",
    "Cancer": "Emotional, nurturing, and protective. Values home and family.",
    "Leo": "Confident, charismatic, and generous. Natural performers and leaders.",
    "Virgo": "Analytical, practical, and detail-oriented. Loves to serve and improve.",
    "Libra": "Charming, fair, and diplomatic. Loves harmony and aesthetics.",
    "Scorpio": "Intense, mysterious, and powerful. Emotionally deep and determined.",
    "Sagittarius": "Optimistic, freedom-loving, and philosophical. Seeks truth and adventure.",
    "Capricorn": "Disciplined, responsible, and ambitious. Values tradition and success.",
    "Aquarius": "Innovative, independent, and humanitarian. Marches to the beat of their own drum.",
    "Pisces": "Empathetic, imaginative, and artistic. Deeply intuitive and spiritual.",
}

# Streamlit UI
st.set_page_config(page_title="Astrological Profile App", page_icon="✨")
st.title("🔮 Discover Your Astrological Profile")

sign = st.selectbox("Choose your zodiac sign:", list(astro_profiles.keys()))

if sign:
    st.subheader(f"♈ Your Astrological Profile for {sign}")
    st.write(astro_profiles[sign])
