import streamlit as st
from datetime import datetime
from pytz import timezone
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

# Function to generate birth chart
def get_astrological_profile(date, time, tz, latitude, longitude):
    dt = Datetime(f"{date} {time}", tz)
    pos = GeoPos(latitude, longitude)
    chart = Chart(dt, pos)

    sun = chart.get(const.SUN)
    moon = chart.get(const.MOON)
    asc = chart.get(const.ASC)

    profile = {
        "Sun Sign": f"{sun.sign} in {sun.house} house",
        "Moon Sign": f"{moon.sign} in {moon.house} house",
        "Rising Sign (Ascendant)": f"{asc.sign}"
    }

    return profile

# App UI
st.set_page_config(page_title="Advanced Astrology Profile", page_icon="✨")
st.title("🔮 Enlightened Astrological Reader")

st.markdown("Enter your birth details for an in-depth astrological reading:")

name = st.text_input("Your Name")
birth_date = st.date_input("Date of Birth")
birth_time = st.time_input("Time of Birth (24h format)")
timezone_str = st.text_input("Time Zone (e.g. 'US/Pacific')", "UTC")
latitude = st.text_input("Latitude (e.g. 34.0522)", "0.0")
longitude = st.text_input("Longitude (e.g. -118.2437)", "0.0")

if st.button("Generate My Profile"):
    try:
        profile = get_astrological_profile(
            birth_date.strftime("%Y/%m/%d"),
            birth_time.strftime("%H:%M"),
            timezone_str,
            latitude,
            longitude
        )
        st.success(f"Astrological Profile for {name or 'You'}")
        for key, value in profile.items():
            st.subheader(key)
            st.write(value)

        st.markdown("✨ *More interpretations and planetary alignments coming soon...*")

    except Exception as e:
        st.error(f"An error occurred: {e}")
