import io
import os
import re

import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, jsonify, render_template, request

# Import your natal chart calculation module
import natal_chart  # Ensure this module is correctly set up

app = Flask(__name__)

# Define the planets and zodiac signs
planets = ["Jupiter", "Mars", "Mercury", "Moon", "Neptune", "Pluto", "Saturn", "Sun", "Uranus", "Venus"]
zodiac_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Planet symbols in Unicode
planet_symbols = {
    "Jupiter": "♃",
    "Mars": "♂",
    "Mercury": "☿",
    "Moon": "☾",
    "Neptune": "♆",
    "Pluto": "♇",
    "Saturn": "♄",
    "Sun": "☉",
    "Uranus": "♅",
    "Venus": "♀"
}

# Define major aspects with their allowable orb (in degrees)
aspects = {
    "Conjunction": 0,
    "Opposition": 180,
    "Trine": 120,
    "Square": 90,
    "Sextile": 60
}

# Define the allowable orb for each aspect
orb = {
    "Conjunction": 8,
    "Opposition": 8,
    "Trine": 8,
    "Square": 8,
    "Sextile": 6
}

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_url = None
    aspect_plot_url = None
    selected_aspects = []

    if request.method == 'POST':
        # Get user inputs for plotting
        positions = {}
        for planet in planets:
            pos = request.form.get(f"{planet}_pos", '')
            if pos:
                positions[planet] = convert_to_degrees(pos)

        # Get selected aspects
        for aspect in aspects:
            if request.form.get(aspect):
                selected_aspects.append(aspect)

        # Generate the plot
        plot_url = generate_plot(positions)
        aspect_plot_url = generate_aspect_plot(positions, selected_aspects)

    return render_template('index.html', planets=planets, plot_url=plot_url,
                           aspect_plot_url=aspect_plot_url, aspects=aspects.keys())

@app.route('/calculate_natal_chart', methods=['POST'])
def calculate_chart():
    data = request.json
    if data is None:
        return jsonify({'error': 'Missing or invalid JSON data'}), 400

    dob = data.get('dob')
    tob = data.get('tob')
    chart_name = data.get('chartName')

    if 'lat' in data and 'lon' in data:
        lat = float(data['lat'])
        lon = float(data['lon'])
    else:
        return jsonify({'error': 'Missing geographic information'}), 400

    try:
        chart = natal_chart.calculate_natal_chart(dob, tob, lat, lon)
        return jsonify({'success': True, 'chart': chart, 'chartName': chart_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def convert_to_degrees(position):
    # Convert position string "20° 26' 27.06" Aries" to degrees as float
    match = re.match(r"(\d+)°\s*(\d+)'?\s*(\d+(?:\.\d+)?)?\"?\s*([A-Za-z]+)", position)
    if match:
        degrees = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3)) if match.group(3) else 0.0
        sign = match.group(4).capitalize()
        total_degrees = degrees + minutes / 60 + seconds / 3600

        # Calculate the degree offset based on the zodiac sign
        sign_index = zodiac_signs.index(sign)
        sign_offset = sign_index * 30

        return total_degrees + sign_offset
    return 0

def generate_plot(positions):
    fig, ax = plt.subplots(figsize=(22, 22), subplot_kw={'projection': 'polar'})

    # Plot the zodiac signs with colors
    num_signs = len(zodiac_signs)
    degrees_per_sign = 360 / num_signs
    colors = plt.cm.tab20(np.linspace(0, 1, num_signs))

    for i, (sign, color) in enumerate(zip(zodiac_signs, colors)):
        angle = (i * degrees_per_sign + degrees_per_sign / 2) * (np.pi / 180)
        ax.text(angle, 1.2, sign, horizontalalignment='center',
                verticalalignment='center', fontsize=19, color=color)

    # Plot the planet positions with symbols
    for planet, degree in positions.items():
        theta = (degree % 360) * (np.pi / 180)  # Convert degrees to radians and normalize
        symbol = planet_symbols[planet]
        ax.text(theta, 1.05, symbol, horizontalalignment='center',
                verticalalignment='center', fontsize=24, color='black')

    # Enhance the plot aesthetics
    ax.set_ylim(0, 1.3)
    ax.set_yticklabels([])
    ax.set_xticks([(i * degrees_per_sign) * (np.pi / 180) for i in range(num_signs)])
    ax.set_xticklabels([])
    ax.grid(color='gray', linestyle='--',
            dashes=(1, 8, 1, 5, 2, 3, 3, 2, 5, 1, 8, 13), linewidth=1)
    ax.spines['polar'].set_visible(False)

    # Save plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)

    # Save the plot to a file in the 'static' directory
    static_dir = 'static'
    plot_path = os.path.join(static_dir, 'plot.png')
    with open(plot_path, 'wb') as f:
        f.write(buf.getbuffer())

    # Return the relative path for HTML
    return '/static/plot.png'

def generate_aspect_plot(positions, selected_aspects):
    fig, ax = plt.subplots(figsize=(22, 22), subplot_kw={'projection': 'polar'})

    # Plot the zodiac signs with colors
    num_signs = len(zodiac_signs)
    degrees_per_sign = 360 / num_signs
    colors = plt.cm.tab20(np.linspace(0, 1, num_signs))

    for i, (sign, color) in enumerate(zip(zodiac_signs, colors)):
        angle = (i * degrees_per_sign + degrees_per_sign / 2) * (np.pi / 180)
        ax.text(angle, 1.2, sign, horizontalalignment='center',
                verticalalignment='center', fontsize=19, color=color)

    # Plot the planet positions with symbols
    planet_angles = {}
    for planet, degree in positions.items():
        theta = (degree % 360) * (np.pi / 180)  # Convert degrees to radians and normalize
        symbol = planet_symbols[planet]
        ax.text(theta, 1.05, symbol, horizontalalignment='center',
                verticalalignment='center', fontsize=24, color='black')
        planet_angles[planet] = theta

    # Plot the selected aspects between planets
    for planet1, angle1 in planet_angles.items():
        for planet2, angle2 in planet_angles.items():
            if planet1 != planet2:
                difference = np.degrees(np.abs(angle1 - angle2))
                if difference > 180:
                    difference = 360 - difference
                for aspect in selected_aspects:
                    aspect_angle = aspects[aspect]
                    if abs(difference - aspect_angle) <= orb[aspect]:
                        ax.plot([angle1, angle2], [1.00, 1.00],
                                linestyle='-', label=aspect, color='black')

    # Enhance the plot aesthetics
    ax.set_ylim(0, 1.3)
    ax.set_yticklabels([])
    ax.set_xticks([(i * degrees_per_sign) * (np.pi / 180) for i in range(num_signs)])
    ax.set_xticklabels([])
    ax.grid(color='gray', linestyle='--',
            dashes=(1, 8, 1, 5, 2, 3, 3, 2, 5, 1, 8, 13), linewidth=1)
    ax.spines['polar'].set_visible(False)

    # Save plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)

    # Save the plot to a file in the 'static' directory
    static_dir = 'static'
    aspect_plot_path = os.path.join(static_dir, 'aspect_plot.png')
    with open(aspect_plot_path, 'wb') as f:
        f.write(buf.getbuffer())
        
    # Return the relative path for HTML
    return '/static/aspect_plot.png'

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
    
@app.route('/calculate_transit_waveform', methods=['POST'])
def calculate_transit_waveform():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Extract parameters
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    natal_positions = data.get('natalPositions')  # Expect degrees as floats

    if not start_date or not end_date or not natal_positions:
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        # Call the transit waveform calculation function
        transit_waveform = natal_chart.calculate_transit_waveform(
            natal_positions=natal_positions,
            start_date=start_date,
            end_date=end_date,
            interval_hours=data.get('intervalHours', 6)
        )
        return jsonify({'success': True, 'waveform': transit_waveform})
    except Exception as e:
        return jsonify({'error': str(e)}), 500