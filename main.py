import io
import os
import re

import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, jsonify, render_template, request
import natal_chart

app = Flask(__name__)

PLANETS = ["Jupiter", "Mars", "Mercury", "Moon", "Neptune", "Pluto", "Saturn", "Sun", "Uranus", "Venus"]
ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

PLANET_SYMBOLS = {
    "Jupiter": "♃", "Mars": "♂", "Mercury": "☿", "Moon": "☾", "Neptune": "♆",
    "Pluto": "♇", "Saturn": "♄", "Sun": "☉", "Uranus": "♅", "Venus": "♀"
}

ASPECTS = {
    "Conjunction": 0, "Opposition": 180, "Trine": 120, "Square": 90, "Sextile": 60
}

ORB = {
    "Conjunction": 8, "Opposition": 8, "Trine": 8, "Square": 8, "Sextile": 6
}


def convert_to_degrees(position):
    match = re.match(r"(\d+)°\s*(\d+)'?\s*(\d+(?:\.\d+)?)?\"?\s*([A-Za-z]+)", position)
    if match:
        degrees = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3)) if match.group(3) else 0.0
        sign = match.group(4).capitalize()
        total_degrees = degrees + minutes / 60 + seconds / 3600
        sign_index = ZODIAC_SIGNS.index(sign)
        return total_degrees + sign_index * 30
    return None


def create_zodiac_plot(ax):
    num_signs = len(ZODIAC_SIGNS)
    degrees_per_sign = 360 / num_signs
    colors = plt.cm.tab20(np.linspace(0, 1, num_signs))
    for i, (sign, color) in enumerate(zip(ZODIAC_SIGNS, colors)):
        angle = (i * degrees_per_sign + degrees_per_sign / 2) * (np.pi / 180)
        ax.text(angle, 1.2, sign, horizontalalignment='center', verticalalignment='center', fontsize=15, color=color)


def save_plot_to_file(fig, filename):
    static_dir = 'static'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    filepath = os.path.join(static_dir, filename)
    fig.savefig(filepath, format='png', bbox_inches='tight', pad_inches=0.1)
    return f"/static/{filename}"


def generate_plot(positions):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
    create_zodiac_plot(ax)
    for planet, degree in positions.items():
        if degree is not None:
            theta = (degree % 360) * (np.pi / 180)
            ax.text(theta, 1.05, PLANET_SYMBOLS[planet], horizontalalignment='center', verticalalignment='center', fontsize=18, color='black')
    ax.set_ylim(0, 1.3)
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.spines['polar'].set_visible(False)
    return save_plot_to_file(fig, 'plot.png')


def generate_aspect_plot(positions, selected_aspects):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
    create_zodiac_plot(ax)
    planet_angles = {planet: (deg % 360) * (np.pi / 180) for planet, deg in positions.items() if deg is not None}
    for planet1, angle1 in planet_angles.items():
        for planet2, angle2 in planet_angles.items():
            if planet1 != planet2:
                diff = np.degrees(np.abs(angle1 - angle2))
                diff = 360 - diff if diff > 180 else diff
                for aspect in selected_aspects:
                    if abs(diff - ASPECTS[aspect]) <= ORB[aspect]:
                        ax.plot([angle1, angle2], [1.0, 1.0], linestyle='-', color='black')
    ax.set_ylim(0, 1.3)
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.spines['polar'].set_visible(False)
    return save_plot_to_file(fig, 'aspect_plot.png')


@app.route('/', methods=['GET', 'POST'])
def index():
    plot_url = aspect_plot_url = None
    selected_aspects = []
    if request.method == 'POST':
        positions = {planet: convert_to_degrees(request.form.get(f"{planet}_pos")) for planet in PLANETS}
        selected_aspects = [aspect for aspect in ASPECTS if request.form.get(aspect)]
        plot_url = generate_plot(positions)
        aspect_plot_url = generate_aspect_plot(positions, selected_aspects)
    return render_template('index.html', planets=PLANETS, plot_url=plot_url, aspect_plot_url=aspect_plot_url, aspects=ASPECTS.keys())


@app.route('/calculate_natal_chart', methods=['POST'])
def calculate_chart():
    data = request.json
    if not data:
        return jsonify({'error': 'Missing or invalid JSON data'}), 400
    try:
        dob = data['dob']
        tob = data['tob']
        lat = float(data['lat'])
        lon = float(data['lon'])
        chart = natal_chart.calculate_natal_chart(dob, tob, lat, lon)
        return jsonify({'success': True, 'chart': chart, 'chartName': data.get('chartName', 'Natal Chart')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)