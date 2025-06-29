# styling_assistant.py

from dataclasses import dataclass
import requests
import csv
from typing import Dict
import tkinter as tk
from tkinter import ttk, messagebox


# --- Data Models ---
@dataclass
class Measurements:
    bust: float        # inches
    waist: float       # inches
    hips: float        # inches
    high_hip: float = None  # optional

@dataclass
class Profile:
    size_category: str
    body_shape: str
    undertone: str = None  # 'Warm', 'Cool', 'Neutral'

# --- Body Size Classification ---
def classify_body_size(m: Measurements) -> str:
    b, w, h = m.bust, m.waist, m.hips
    if 33.5 <= b <= 34.5 and 25 <= w <= 26 and 36 <= h <= 37:
        return "Small"
    elif 35.5 <= b <= 37.5 and 27 <= w <= 28 and 38 <= h <= 39:
        return "Medium"
    elif 38 <= b <= 39.5 and 29.5 <= w <= 31 and 40.5 <= h <= 42:
        return "Large"
    avg = (b + w + h) / 3
    return "Small" if avg < 36 else "Medium" if avg < 40 else "Large"

# --- Body Shape Classification ---
def classify_body_shape(m: Measurements) -> str:
    b, w, h, hh = m.bust, m.waist, m.hips, m.high_hip
    if abs(b - h) <= 1 and (b - w >= 9 or h - w >= 10):
        return "Hourglass"
    if hh and h - b >= 3.6 and h - w < 9:
        return "Pear"
    if abs(b - h) < 3.6 and b - w < 9 and h - w < 10:
        return "Rectangle"
    if b - h >= 3.6 and b - w < 9:
        return "Inverted Triangle"
    return "Undefined"

# --- Color by Body Size Guidance ---
def color_suggestions_by_size(size: str) -> dict:
    rec = {}
    if size == "Large":
        rec['Large Body Size'] = (
            "Dark colors (black, navy, deep greens) create a slimming silhouette."
        )
    elif size == "Small":
        rec['Small Body Size'] = (
            "Light, bright colors (whites, pastels, vibrant hues) add presence."
        )
    elif size == "Medium":
        rec['Medium Body Size'] = (
            "Balanced tones maintain natural proportions."
        )
    return rec

# --- Skin Tone Guidance ---
def color_palette_for_undertone(undertone: str) -> dict:
    rec = {}
    if undertone == 'Warm':
        rec['Warm Undertones'] = "Coral, peach, golden yellow, olive green."
    elif undertone == 'Cool':
        rec['Cool Undertones'] = "Emerald green, ruby red, sapphire blue."
    elif undertone == 'Neutral':
        rec['Neutral Undertones'] = "Dusty pink, jade, taupe, creamy neutrals."
    return rec

# --- Shape-Specific Print Tips ---
def print_recommendations(shape: str) -> dict:
    rec = {}
    if shape == 'Pear':
        rec['Pear Shape'] = "Bold prints on top; solids or small/vertical prints below."
    elif shape == 'Hourglass':
        rec['Hourglass Shape'] = "Waist-accentuating prints; avoid boxy cuts."
    elif shape == 'Rectangle':
        rec['Rectangle Shape'] = "Adds curves with prints or ruffles at bust & hips."
    elif shape == 'Inverted Triangle':
        rec['Inverted Triangle'] = "Keep upper simple; prints on lower body."
    rec['Universal'] = "Monochromatic prints are slimming and versatile."
    return rec

# --- Weather-Based Dressing ---
def dress_for_weather(temp_c: float, cond: str) -> dict:
    rec = {}
    # guidance omitted for brevity; same as before
    lc = cond.lower()
    if 'rain' in lc:
        rec['Rain Gear'] = "Waterproof jacket and water‑resistant footwear."
    if 'snow' in lc or 'wind' in lc:
        rec['Protection'] = "Windproof layers, cover extremities."
    if temp_c >= 25 and 'sun' in lc:
        rec['Sun Care'] = "Hat, sunglasses, sunscreen."
    return rec

# --- Occasion-Based Dressing ---
def dress_for_occasion(occasion: str) -> dict:
    rec = {}
    oc = occasion.lower()
    if  'gala' in oc :
        rec['Formal'] = "Gowns, cocktail dresses, elegant suits."
    if 'business formal' in oc:
        rec['Business Formal'] = "Tailored suit, dress pants/skirts, blouses."
    if 'semi-formal' in oc:
        rec['Semi‑Formal'] = "Cocktail dress or stylish jumpsuit; add blazer."
    if 'casual' in oc and 'business' in oc:
        rec['Business Casual'] = "Chinos + button-down or blazer + jeans."
    elif 'casual' in oc:
        rec['Casual'] = "Jeans, comfortable dresses; functional for outdoors."
    return rec

# --- Save Outfit to CSV ---
def save_outfit_to_csv(filename: str, outfit: Dict):
    file_exists = False
    try:
        with open(filename, 'r', newline='') as f:
            file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=outfit.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(outfit)

# --- Weather Fetch ---
def fetch_weather(api_key: str, city: str) -> tuple:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    api_key = "4e441abf6085898180f8f8baf17f74f6"
    r = requests.get(url).json()
    return r['main']['temp'], r['weather'][0]['main']


def on_submit(bust, waist, hips, highhip, tone, occasion, city, api_key, result_text):
    # Validate measurements
    try:
        m = Measurements(float(bust), float(waist), float(hips),
                         float(highhip) if highhip.strip() else None)
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers for measurements.")
        return

    if tone not in ("Warm", "Cool", "Neutral"):
        messagebox.showerror("Input Error", "Skin tone must be Warm, Cool, or Neutral.")
        return

    # Build profile
    profile = Profile(
        size_category=classify_body_size(m),
        body_shape=classify_body_shape(m),
        undertone=tone
    )

    # Fetch weather
    try:
        temp, cond = fetch_weather(api_key, city)
    except Exception as e:
        messagebox.showerror("Weather Error", f"Could not fetch weather: {e}")
        return

    temp = round(temp)
    weather_rec = dress_for_weather(temp, cond)

    # Compute recommendations
    size_colors = color_suggestions_by_size(profile.size_category)
    tone_colors = color_palette_for_undertone(profile.undertone)
    print_tips = print_recommendations(profile.body_shape)
    occasion_rec = dress_for_occasion(occasion)

    # Display results
    lines = [
        f"Size: {profile.size_category}",
        f"Body Shape: {profile.body_shape}",
        f"Undertone: {profile.undertone}",
        f"Occasion: {occasion}",
        f"Weather in {city}: {temp}°C, {cond}\n",
        "Color by Body Size:", *size_colors.values(),
        "Color by Skin Tone:", *tone_colors.values(),
        "Print tips:", *print_tips.values(),
        "Occasion pick:", *occasion_rec.values(),
        "Weather-specific picks:", *weather_rec.values()
    ]
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, "\n".join(lines))

    # Save to CSV
    outfit = {
        "Size": profile.size_category,
        "Shape": profile.body_shape,
        "Undertone": profile.undertone,
        "Occasion": occasion,
        "City": city,
        "Temp": temp, "Weather": cond,
        "SizeColors": "; ".join(size_colors.values()),
        "ToneColors": "; ".join(tone_colors.values()),
        "PrintTips": "; ".join(print_tips.values()),
        "OccasionTips": "; ".join(occasion_rec.values()),
        "WeatherTips": "; ".join(weather_rec.values())
    }
    save_outfit_to_csv("saved_outfits.csv", outfit)
    messagebox.showinfo("Success", "Recommendations saved to CSV.")


def run_app():    
    root = tk.Tk()
    root.title("Styling Assistant")
    root.geometry("600x400")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    labels = ["Bust (in)", "Waist (in)", "Hips (in)", "High-hip (optional)",
              "Skin Tone", "Occasion", "City ", "API Key"]
    vars_ = [tk.StringVar() for _ in labels]

    for i, text in enumerate(labels):
        ttk.Label(frame, text=text + ":").grid(row=i, column=0, sticky="E", pady=5, padx=5)
        if text == "Skin Tone":
            ttk.Combobox(frame, textvariable=vars_[i],
                         values=["Warm", "Cool", "Neutral"], state="readonly"
            ).grid(row=i, column=1, sticky="WE")
        else:
            show = "*" if text == "API Key" else ""
            ttk.Entry(frame, textvariable=vars_[i], show=show).grid(row=i, column=1, sticky="WE")

    result_text = tk.Text(frame, height=15, wrap="word")
    result_text.grid(row=len(labels)+1, column=0, columnspan=2, sticky="WE", pady=5)

    submit_btn = ttk.Button(
        frame, text="Submit",
        command=lambda: on_submit(
            *(v.get() for v in vars_), result_text
        )
    )
    submit_btn.grid(row=len(labels), column=0, columnspan=2, sticky="WE", pady=10)

    frame.grid_columnconfigure(1, weight=1)
    root.mainloop()

if __name__ == "__main__":
    run_app()