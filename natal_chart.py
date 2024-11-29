import datetime
import pytz
import swisseph as swe
from timezonefinder import TimezoneFinder


def degrees_to_dms(degrees):
    """Convert decimal degrees to DMS (Degrees, Minutes, Seconds) format."""
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = (degrees - d - m / 60) * 3600
    return f"{d}° {m}' {s:.2f}\""


def degrees_to_zodiac(degrees):
    """Convert decimal degrees to Zodiac position."""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
        "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign = signs[int(degrees // 30)]
    position_in_sign = degrees % 30
    return f"{degrees_to_dms(position_in_sign)} {sign}"


def get_timezone(lat, lon):
    """Retrieve timezone for a given latitude and longitude."""
    tz_finder = TimezoneFinder()
    timezone_str = tz_finder.timezone_at(lat=lat, lng=lon)
    if not timezone_str:
        raise ValueError("Could not determine timezone for the given location.")
    return timezone_str


def calculate_natal_chart(dob, tob, lat, lon):
    """
    Calculate a natal chart given date/time of birth and location.

    Args:
        dob (str): Date of birth in the format 'DD.MM.YYYY'.
        tob (str): Time of birth in the format 'HH:MM'.
        lat (float): Latitude of the birth location.
        lon (float): Longitude of the birth location.

    Returns:
        dict: Planetary positions in the zodiac.
    """
    try:
        # Convert local time to UTC and calculate Julian day
        local_dt = datetime.datetime.strptime(f"{dob} {tob}", "%d.%m.%Y %H:%M")
        timezone_str = get_timezone(lat, lon)
        local_tz = pytz.timezone(timezone_str)
        local_dt = local_tz.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.utc)
        julian_day = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0)

        # Calculate planetary positions
        swe.set_topo(lon, lat, 0)
        bodies = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
            "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS,
            "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
        }

        positions = {}
        for body, code in bodies.items():
            position, _ = swe.calc_ut(julian_day, code)  # Extract first element of the tuple
            positions[body] = degrees_to_zodiac(position)
        return positions

    except Exception as e:
        raise RuntimeError(f"Error calculating natal chart: {e}")