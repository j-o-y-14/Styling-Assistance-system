import streamlit as st
from dataclasses import dataclass
import requests
import openai
import os

DEFAULT_API_KEY = "4e441abf6085898180f8f8baf17f74f6"
OPENAI_API_KEY = "your-openai-api-key"
openai.api_key = OPENAI_API_KEY

@dataclass
class Measurements:
    bust: float
    waist: float
    hips: float
    high_hip: float = None

def cm_to_inches(cm: float) -> float:
    return cm / 2.54

def classify_body_size(m: Measurements) -> str:
    avg = (m.bust + m.waist + m.hips) / 3
    if avg < 36:
        return "Small"
    elif avg < 40:
        return "Medium"
    else:
        return "Large"

def classify_body_shape(m: Measurements) -> str:
    b, w, h = m.bust, m.waist, m.hips
    if abs(b - h) <= 1 and (b - w >= 9 or h - w >= 10):
        return "Hourglass"
    elif h - b >= 3.6 and h - w < 9:
        return "Pear"
    elif b - h >= 3.6 and b - w < 9:
        return "Inverted Triangle"
    elif abs(b - h) < 3.6 and b - w < 9 and h - w < 10:
        return "Rectangle"
    else:
        return "Undefined"

def print_recommendations(shape: str) -> str:
    return {
        "Hourglass": "Fitted styles that emphasize the waist",
        "Pear": "Bold tops and A-line skirts",
        "Rectangle": "Add curves with belts and layers",
        "Inverted Triangle": "Simple tops with detailed bottoms"
    }.get(shape, "Experiment with patterns and balance.")

def fetch_weather(city: str) -> tuple:
    try:
        r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={DEFAULT_API_KEY}").json()
        return r["main"]["temp"], r["weather"][0]["main"]
    except:
        return None, None

def dress_for_weather(temp_c: float, cond: str) -> str:
    rec = []
    if temp_c >= 25:
        rec.append("Light fabrics + sun care.")
    elif temp_c >= 15:
        rec.append("Cotton layers.")
    elif temp_c >= 5:
        rec.append("Sweaters + jacket.")
    else:
        rec.append("Coats & thermals.")
    lc = cond.lower()
    if "rain" in lc:
        rec.append("Waterproof jacket.")
    if "snow" in lc or "wind" in lc:
        rec.append("Cover extremities.")
    return "; ".join(rec)

def dress_for_occasion(oc: str) -> str:
    o = oc.lower()
    if "black-tie" in o:
        return "Elegant gown or formal suit."
    if "cocktail" in o:
        return "Dress or jumpsuit with heels."
    if "dressy casual" in o:
        return "Smart top and tailored pants."
    return "Comfy casual outfit."

def generate_outfit_suggestion(size, shape, occasion, weather, temp):
    prompt = f"""Suggest an outfit for a person with a {shape} body shape and {size} body size. The occasion is {occasion}, and the weather is {weather} with {temp}°C."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message['content']

st.set_page_config(page_title="Styling Assistant", layout="centered")
st.markdown("""
    <style>
        .main {
            background-color: #faf3f3;
            padding: 2rem;
            border-radius: 20px;
        }
        h1, h2, h3 {
            color: #dc6c85;
        }
    </style>
""", unsafe_allow_html=True)

st.title("👗 Welcome to Your Styling Assistant")
st.subheader("✨ Personalize Your Style with Confidence")
st.write("Enter your body measurements to get personalized fashion advice!")

if os.path.exists("body_shapes.png"):
    st.image("body_shapes.png", caption="Body Shape Types", use_container_width=True)
else:
    st.warning("Image 'body_shapes.png' not found.")

st.markdown("---")

with st.form("measurement_form"):
    st.subheader("📏 Input Your Measurements")
    unit = st.radio("Choose unit", ["in", "cm"])
    bust = st.number_input("Bust", min_value=0.0)
    waist = st.number_input("Waist", min_value=0.0)
    hips = st.number_input("Hips", min_value=0.0)
    high_hip = st.number_input("High Hip (optional)", min_value=0.0, value=0.0)
    submitted = st.form_submit_button("Submit Measurements")

if submitted:
    if unit == "cm":
        bust = cm_to_inches(bust)
        waist = cm_to_inches(waist)
        hips = cm_to_inches(hips)
        high_hip = cm_to_inches(high_hip)
    else:
        high_hip = high_hip if high_hip != 0 else None
    m = Measurements(bust, waist, hips, high_hip)
    size = classify_body_size(m)
    shape = classify_body_shape(m)
    tip = print_recommendations(shape)

    st.markdown("---")
    st.subheader("📊 Your Results")
    st.success(f"Body Size: {size}\n\nBody Shape: {shape}")
    st.info(f"💡 Style Tip: {tip}")

    outfit_text = f"""Outfit Suggestion:\nBody Size: {size}\nBody Shape: {shape}\n\nStyle Tip: {tip}"""

    if os.path.exists("outfit_ideas.png"):
        st.image("outfit_ideas.png", caption="Outfit Ideas for Your Shape", use_container_width=True)
    else:
        st.warning("Image 'outfit_ideas.png' not found.")

    st.markdown("---")
    with st.expander("🌦️ Get Advice for Weather and Occasion"):
        city = st.text_input("Enter your city")
        occasion = st.selectbox("Select Occasion", ["Black-tie", "Cocktail", "Dressy Casual", "Casual"])
        if st.button("Get Advice"):
            temp, cond = fetch_weather(city)
            if temp is not None:
                st.write(f"Weather in {city}: {temp}°C, {cond}")
                st.write(f"🌤️ Weather Tip: {dress_for_weather(temp, cond)}")
                st.write(f"🌟 Occasion Tip: {dress_for_occasion(occasion)}")
                suggestion = generate_outfit_suggestion(size, shape, occasion, cond, temp)
                st.markdown(f"🧐 **AI Suggestion:** {suggestion}")

                # Combine everything for download
                outfit_text += f"\n\nOccasion: {occasion}\nWeather: {cond}, {temp}°C\n\nSuggested Outfit:\n{suggestion}"

                # Download Button
                st.download_button(
                    label="📅 Download My Outfit Suggestion",
                    data=outfit_text,
                    file_name="my_outfit_suggestion.txt",
                    mime="text/plain"
                )
            else:
                st.error("❌ Could not fetch weather. Check city name.")

