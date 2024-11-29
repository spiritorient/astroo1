import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import natal_chart  # Reuse your natal_chart module for transit position calculations

# Define planets, aspects, and orbs
planets = ["Jupiter", "Mars", "Mercury", "Moon", "Neptune", "Pluto",
           "Saturn", "Sun", "Uranus", "Venus"]
aspects = {"Conjunction": 0, "Opposition": 180, "Trine": 120,
           "Square": 90, "Sextile": 60}
orb = {"Conjunction": 8, "Opposition": 8, "Trine": 8,
       "Square": 8, "Sextile": 6}

def calculate_transit_waveforms(natal_positions, start_date, end_date):
    """
    Calculate transit interactions for a natal chart over a date range.
    """
    print(f"Calculating transit waveforms from {start_date} to {end_date}")
    current_date = start_date
    transits = []

    while current_date <= end_date:
        for planet in planets:
            transit_position = natal_chart.get_transit_position(current_date, planet)

            for natal_planet, natal_position in natal_positions.items():
                for aspect_name, exact_angle in aspects.items():
                    angle_diff = abs((transit_position - natal_position) % 360)
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff  # Normalize angle difference

                    if angle_diff <= orb[aspect_name]:  # Within orb
                        intensity = 1 - angle_diff / orb[aspect_name]
                        transits.append({
                            'date': current_date,
                            'transiting_planet': planet,
                            'natal_planet': natal_planet,
                            'aspect': aspect_name,
                            'intensity': intensity,
                        })
                        print(f"Transit: {transits[-1]}")

        current_date += timedelta(days=1)

    print(f"Total transits calculated: {len(transits)}")
    return transits

def generate_transit_waveform_plot(transits, start_date, end_date):
    """
    Generate a high-resolution waveform plot based on transit data.
    """
    print("Generating transit waveform plot...")
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    intensity_data = {}
    for t in transits:
        key = f"{t['transiting_planet']} {t['aspect']} {t['natal_planet']}"
        if key not in intensity_data:
            intensity_data[key] = [0] * len(dates)
        index = (t['date'] - start_date).days
        intensity_data[key][index] = t['intensity']

    print(f"Prepared intensity data.")

    # Increase figure size and DPI for higher resolution
    fig, ax = plt.subplots(figsize=(18, 9), dpi=200)  # Adjust figsize and dpi as needed

    for label, intensity in intensity_data.items():
        ax.plot(dates, intensity, label=label)

    ax.set_title("Transit Waveforms", fontsize=16)
    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Intensity", fontsize=14)
    ax.legend(loc='upper right', fontsize='small')
    ax.grid(True)

    static_dir = 'static'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    plot_path = os.path.join(static_dir, 'transit_waveforms.png')
    plt.savefig(plot_path, format='png', bbox_inches='tight')
    plt.close(fig)

    print(f"Plot saved to {plot_path}")
    return '/static/transit_waveforms.png'