import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog
from ttkbootstrap.tooltip import ToolTip
from dataclasses import dataclass
import threading, queue, csv, requests, tkinter as tk
from tkinter import messagebox
import json, os

DEFAULT_API_KEY = "4e441abf6085898180f8f8baf17f74f6"
PROFILE_FILE = "profiles.json"
LATEST_TIP = {}  # Holds the most recent suggestion shown

@dataclass
class Measurements:
    bust: float
    waist: float
    hips: float
    high_hip: float = None

@dataclass
class Profile:
    size_category: str
    body_shape: str
    undertone: str

def cm_to_inches(cm: float) -> float:
    return cm / 2.54

def classify_body_size(m: Measurements) -> str:
    b, w, h = m.bust, m.waist, m.hips
    avg = (b + w + h) / 3
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

def color_suggestions_by_size(size: str) -> str:
    return {
        "Small": "Light colors and playful patterns",
        "Medium": "Balanced tones with structure",
        "Large": "Dark slimming colors and clean lines"
    }.get(size, "")

def color_palette_for_undertone(undertone: str) -> str:
    return {
        "Warm": "Coral, peach, warm red, olive",
        "Cool": "Emerald green, navy, pink, gray",
        "Neutral": "Taupe, blush, jade, soft white"
    }.get(undertone, "")

def print_recommendations(shape: str) -> str:
    return {
        "Hourglass": "Fitted styles that emphasize the waist",
        "Pear": "Bold tops and A-line skirts",
        "Rectangle": "Add curves with belts and layers",
        "Inverted Triangle": "Simple tops with detailed bottoms"
    }.get(shape, "Experiment with patterns and balance.")

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

def save_outfit_to_csv(outfit: dict):
    file = "saved_outfits.csv"
    exists = os.path.exists(file)
    with open(file, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, outfit.keys())
        if not exists:
            w.writeheader()
        w.writerow(outfit)

def fetch_weather(api_key: str, city: str) -> tuple:
    try:
        r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}").json()
        return r["main"]["temp"], r["weather"][0]["main"]
    except:
        return None, None

def show_splash():
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.geometry("500x350+500+250")
    splash.configure(bg="#800080")
    label = tk.Label(splash, text="Styling Assistant", font=("Segoe UI", 24, "bold"), fg="white", bg="#800080")
    label.pack(expand=True, pady=20)
    desc = tk.Label(
        splash,
        text="Get personalized fashion tips based on your body and the weather!",
        font=("Segoe UI", 16, "bold"),
        fg="white",
        bg="#800080"
    )
    desc.pack(pady=10)
    splash.after(2500, splash.destroy)
    splash.mainloop()

def show_step():
    for widget in root.winfo_children():
        widget.destroy()

    frame = ttk.Frame(root, padding=20)
    frame.pack(expand=True)

    header = ttk.Frame(frame)
    header.pack(pady=(0, 20))
    ttk.Label(header, text="👗 Welcome to Your Styling Assistant", font=("Helvetica", 18, "bold"), bootstyle="primary").pack()
    ttk.Label(header, text="✨ Personalize Your Style with Confidence", font=("Segoe UI", 14, "bold"), foreground="white").pack(pady=5)

    ttk.Separator(frame, orient="horizontal").pack(fill='x', pady=10)
    ttk.Label(frame, text="🧠 Recommendations according to body size and shape", font=("Helvetica", 14, "bold"), bootstyle="info").pack(pady=10)
    ttk.Label(frame, text="📏 Step 1: Enter Your Measurements", font=("Helvetica", 16, "bold"), bootstyle="info").pack(pady=10)

    unit_var = tk.StringVar(value="in")
    unit_row = ttk.Frame(frame)
    unit_row.pack(pady=5)
    ttk.Label(unit_row, text="Unit:").pack(side="left")
    unit_option = ttk.Combobox(unit_row, textvariable=unit_var, values=["in", "cm"], width=10)
    unit_option.pack(side="left", padx=5)

    entries = {}
    for label in ["Bust", "Waist", "Hips", "High Hip (optional)"]:
        lbl = ttk.Label(frame, text=label)
        lbl.pack()
        entry = ttk.Entry(frame)
        entry.pack(fill='x', padx=20, pady=2)
        ToolTip(entry, text=f"Enter your {label.lower()} measurement")
        entries[label] = entry

    def analyze():
        try:
            bust = float(entries["Bust"].get())
            waist = float(entries["Waist"].get())
            hips = float(entries["Hips"].get())
            high_hip = entries["High Hip (optional)"].get()
            high_hip = float(high_hip) if high_hip else None
            if unit_var.get() == "cm":
                bust = cm_to_inches(bust)
                waist = cm_to_inches(waist)
                hips = cm_to_inches(hips)
                if high_hip:
                    high_hip = cm_to_inches(high_hip)
            m = Measurements(bust, waist, hips, high_hip)
            size = classify_body_size(m)
            shape = classify_body_shape(m)
            tip = print_recommendations(shape)
            global LATEST_TIP
            LATEST_TIP = {"size": size, "shape": shape, "tip": tip}
            show_profile_summary()
        except Exception as e:
            messagebox.showerror("Input Error", f"Please enter valid numbers.\n{e}")

    ttk.Button(frame, text="✅ Continue", command=analyze, bootstyle="primary-outline").pack(pady=10)

def show_profile_summary():
    for widget in root.winfo_children():
        widget.destroy()

    frame = ttk.Frame(root, padding=20)
    frame.pack(expand=True)

    card = ttk.Labelframe(frame, text="Your Styling Profile Summary", padding=15, bootstyle="dark")
    card.pack(fill='both', expand=True)

    ttk.Label(card, text=f"Body Size: {LATEST_TIP.get('size', 'N/A')}", font=("Segoe UI", 16, "bold"), foreground="white").pack(pady=5)
    ttk.Label(card, text=f"Body Shape: {LATEST_TIP.get('shape', 'N/A')}", font=("Segoe UI", 16, "bold"), foreground="white").pack(pady=5)
    ttk.Label(card, text=f"Pattern recommendation according to body shape: {LATEST_TIP.get('tip', '')}", font=("Segoe UI", 14), foreground="white", wraplength=500).pack(pady=10)
    ttk.Label(card, text=f"Color Recommendation according to body type: {color_suggestions_by_size(LATEST_TIP.get('size', ''))}", font=("Segoe UI", 14), foreground="white", wraplength=500).pack(pady=10)

    ttk.Button(card, text="🎯 Get Further Advice", command=show_weather_or_occasion_step, bootstyle="success-outline").pack(pady=10)
    ttk.Button(card, text="🔁 Start Over", command=show_step, bootstyle="secondary-outline").pack(pady=5)

def show_weather_or_occasion_step():
    for widget in root.winfo_children():
        widget.destroy()

    frame = ttk.Frame(root, padding=20)
    frame.pack(expand=True)

    ttk.Label(frame, text="🌦️ Styling Recommendations According to Weather, Occasion, and Undertone", font=("Helvetica", 16, "bold"), bootstyle="info").pack(pady=10)

    row = ttk.Frame(frame)
    row.pack(pady=10, fill='x')
    ttk.Label(row, text="City:", width=20).pack(side='left')
    city_entry = ttk.Entry(row)
    city_entry.pack(side='left', expand=True, fill='x')
    ToolTip(city_entry, text="Enter your city to get live weather advice")

    row2 = ttk.Frame(frame)
    row2.pack(pady=5, fill='x')
    ttk.Label(row2, text="Occasion:", width=20).pack(side='left')
    occasion_var = tk.StringVar()
    occasion_entry = ttk.Combobox(row2, textvariable=occasion_var, values=["Black-tie", "Cocktail", "Dressy Casual", "Casual"])
    occasion_entry.pack(side='left', expand=True, fill='x')

    undertone_var = tk.StringVar()
    ttk.Label(frame, text="Skin Undertone (Warm / Cool / Neutral):").pack(pady=(10, 0))
    undertone_entry = ttk.Entry(frame, textvariable=undertone_var)
    undertone_entry.pack(fill='x', padx=20, pady=5)
    ToolTip(undertone_entry, text="Enter your undertone (e.g., Warm, Cool, Neutral)")

    output = ScrolledText(frame, height=10, font=("Segoe UI", 12), background="#2c2f33", foreground="white", insertbackground="white", borderwidth=2, relief="groove")
    output.pack(pady=10, fill='both', expand=True)

    def get_advice():
        city = city_entry.get()
        temp, cond = fetch_weather(DEFAULT_API_KEY, city)
        if temp is not None:
            output.insert('end', f"Weather in {city}: {temp}°C, {cond}\n")
            output.insert('end', f"Body recommendation according to weather: {dress_for_weather(temp, cond)}\n")
        else:
            output.insert('end', f"Could not fetch weather for {city}.\n")
        occ = occasion_entry.get()
        output.insert('end', f"Body recommendation according to occasion: {dress_for_occasion(occ)}\n")
        undertone = undertone_var.get().strip().capitalize()
        color_tip = color_palette_for_undertone(undertone)
        output.insert('end', f"Body recommendation according to undertone: {color_tip}\n")

    ttk.Button(frame, text="🎨 Get Advice", command=get_advice, bootstyle="success").pack(pady=10)
    ttk.Button(frame, text="💾 Save Tips", command=lambda: save_outfit_to_csv({"City": city_entry.get(), "Occasion": occasion_entry.get(), "Tips": output.get("1.0", "end").strip()})).pack()
    ttk.Button(frame, text="⬅️ Back", command=show_profile_summary, bootstyle="secondary-outline").pack(pady=5)
    ttk.Button(frame, text="🔁 Start Over", command=show_step, bootstyle="warning-outline").pack(pady=5)

if __name__ == '__main__':
    show_splash()
    root = ttk.Window(themename="cyborg")
    root.title("Styling Assistant")
    root.geometry("700x600")
    show_step()
    root.mainloop()
