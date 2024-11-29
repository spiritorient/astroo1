from datetime import datetime
import io
import os
import re

import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, jsonify, render_template, request

# Import natal chart calculation and transit waveform modules
import natal_chart  # Ensure this module is correctly set up
import transit_waveforms  # Transit waveform calculation module

app = Flask(__name__)

# Define the planets and zodiac signs
planets = ["Jupiter", "Mars", "Mercury", "Moon", "Neptune",
           "Pluto", "Saturn", "Sun", "Uranus", "Venus"]
zodiac_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

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
orb = {
    "Conjunction": 8,
    "Opposition": 8,
    "Trine": 8,
    "Square": 8,
    "Sextile": 6
}

# --- ROUTES ---


@app.route('/')
def index():
    # Render the index.html with aspect options and planets
    return render_template('index.html', planets=planets, aspects=aspects.keys())


@app.route('/calculate_natal_chart', methods=['POST'])
def calculate_chart():
    """
    Endpoint to calculate the natal chart.
    """
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


@app.route('/generate_plot', methods=['POST'])
def generate_zodiac_plot():
    """
    Generate zodiac and aspect plots based on user input.
    """
    try:
        data = request.json
        positions = data.get('positions')  # Expecting {planet: position strings}
        selected_aspects = data.get('aspects', [])

        # Convert position strings to degrees
        for planet, pos_str in positions.items():
            positions[planet] = convert_to_degrees(pos_str)

        # Generate plots
        plot_url = generate_plot(positions)
        aspect_plot_url = generate_aspect_plot(positions, selected_aspects)

        return jsonify({'plot_url': plot_url, 'aspect_plot_url': aspect_plot_url})
    except Exception as e:
        print(f"Error: {e}")  # Print error for debugging
        return jsonify({'error': str(e)}), 500


@app.route('/transit_waveforms', methods=['POST'])
def transit_waveforms_route():
    """
    Calculate and render transit waveforms on a timeline.
    """
    try:
        data = request.json
        natal_chart_positions = data.get('natal_chart')  # Natal chart as {planet: position strings}
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        selected_transiting_planets = data.get('transiting_planets')  # List of transiting planets
        selected_aspects = data.get('aspects')  # List of aspects

        if not natal_chart_positions or not start_date or not end_date or not selected_transiting_planets or not selected_aspects:
            return jsonify({'error': 'Invalid input data'}), 400

        # Convert natal chart positions from strings to degrees
        natal_positions = {}
        for planet, pos_str in natal_chart_positions.items():
            natal_positions[planet] = convert_to_degrees(pos_str)

        # Use the transit_waveforms module for calculations
        transits = transit_waveforms.calculate_transit_waveforms(
            natal_positions, start_date, end_date, selected_transiting_planets, selected_aspects)

        # Generate waveform plot
        plot_url = transit_waveforms.generate_transit_waveform_plot(
            transits, start_date, end_date)
        return jsonify({'plot_url': plot_url})

    except Exception as e:
        print(f"Error: {e}")  # Print error for debugging
        return jsonify({'error': str(e)}), 500

# --- HELPER FUNCTIONS ---


def convert_to_degrees(position):
    """
    Convert position string like '20° 26\' 27.06" Aries' to degrees as float.
    """
    # Enhanced regex pattern
    pattern = r"""
        (\d+\.?\d*)        # Degrees, which can be integer or float
        °\s*
        (?:(\d+\.?\d*)')?  # Optional minutes
        \s*
        (?:(\d+\.?\d*)")?  # Optional seconds
        \s*
        ([A-Za-z]+)        # Zodiac sign
    """
    match = re.match(pattern, position.strip(), re.VERBOSE)
    if match:
        degrees = float(match.group(1))
        minutes = float(match.group(2)) if match.group(2) else 0.0
        seconds = float(match.group(3)) if match.group(3) else 0.0
        sign = match.group(4).capitalize()
        total_degrees = degrees + minutes / 60 + seconds / 3600

        # Calculate the degree offset based on the zodiac sign
        try:
            sign_index = zodiac_signs.index(sign)
            sign_offset = sign_index * 30
        except ValueError:
            raise ValueError(f"Invalid zodiac sign: '{sign}' in position '{position}'")

        return total_degrees + sign_offset
    else:
        raise ValueError(f"Invalid position format: '{position}'")


def generate_plot(positions):
    """
    Generate a zodiac chart plot.
    """
    fig, ax = plt.subplots(figsize=(22, 22), subplot_kw={'projection': 'polar'})

    # Plot the zodiac signs
    num_signs = len(zodiac_signs)
    degrees_per_sign = 360 / num_signs
    colors = plt.cm.tab20(np.linspace(0, 1, num_signs))

    for i, (sign, color) in enumerate(zip(zodiac_signs, colors)):
        angle = (i * degrees_per_sign + degrees_per_sign / 2) * (np.pi / 180)
        ax.text(angle, 1.2, sign, horizontalalignment='center',
                verticalalignment='center', fontsize=19, color=color)

    # Plot planet positions
    for planet, degree in positions.items():
        theta = (degree % 360) * (np.pi / 180)
        symbol = planet_symbols[planet]
        ax.text(theta, 1.05, symbol, horizontalalignment='center',
                verticalalignment='center', fontsize=24, color='black')

    ax.set_ylim(0, 1.3)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(color='gray', linestyle='--', linewidth=1)
    ax.spines['polar'].set_visible(False)

    # Save the plot
    plot_path = os.path.join('static', 'plot.png')
    plt.savefig(plot_path, format='png', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    return '/static/plot.png'


def generate_aspect_plot(positions, selected_aspects):
    """
    Generate a polar aspect plot based on selected aspects between planets.
    """
    fig, ax = plt.subplots(figsize=(22, 22), subplot_kw={'projection': 'polar'})

    # Plot the zodiac signs
    num_signs = len(zodiac_signs)
    degrees_per_sign = 360 / num_signs
    colors = plt.cm.tab20(np.linspace(0, 1, num_signs))

    for i, (sign, color) in enumerate(zip(zodiac_signs, colors)):
        angle = (i * degrees_per_sign + degrees_per_sign / 2) * (np.pi / 180)
        ax.text(angle, 1.2, sign, horizontalalignment='center',
                verticalalignment='center', fontsize=19, color=color)

    # Plot planet positions
    planet_angles = {}
    for planet, degree in positions.items():
        theta = (degree % 360) * (np.pi / 180)
        symbol = planet_symbols[planet]
        ax.text(theta, 1.05, symbol, horizontalalignment='center',
                verticalalignment='center', fontsize=24, color='black')
        planet_angles[planet] = theta

    # Plot aspects
    for planet1, angle1 in planet_angles.items():
        for planet2, angle2 in planet_angles.items():
            if planet1 != planet2:
                difference = abs(np.degrees(angle1 - angle2))
                if difference > 180:
                    difference = 360 - difference
                for aspect in selected_aspects:
                    aspect_angle = aspects[aspect]
                    if abs(difference - aspect_angle) <= orb[aspect]:
                        ax.plot([angle1, angle2], [1.0, 1.0],
                                linestyle='-', color='black')

    ax.set_ylim(0, 1.3)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(color='gray', linestyle='--', linewidth=1)
    ax.spines['polar'].set_visible(False)

    aspect_plot_path = os.path.join('static', 'aspect_plot.png')
    plt.savefig(aspect_plot_path, format='png',
                bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    return '/static/aspect_plot.png'

# --- APP RUN ---
if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)