import requests

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

def fetch_weather(lat, lon, days=3, timezone="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,et0_fao_evapotranspiration,temperature_2m_max,temperature_2m_min",
        "timezone": timezone,
        "forecast_days": days
    }
    r = requests.get(OPEN_METEO_BASE, params=params, timeout=10)
    r.raise_for_status()
    js = r.json()
    daily = js.get("daily", {})
    dates = daily.get("time", [])
    precip = daily.get("precipitation_sum", [0]*len(dates))
    et0 = daily.get("et0_fao_evapotranspiration", [None]*len(dates))
    out = []
    for d, p, e in zip(dates, precip, et0):
        out.append({"date": d, "precip_mm": p, "et0_mm": e})
    return out

def decide_irrigation(weather, kc=0.9, area_m2=100, flow_rate_lpm=10):
    first = weather[0]
    et0 = first["et0_mm"] if first["et0_mm"] is not None else 4.0
    etc = kc * et0
    rain = first["precip_mm"]
    need_mm = max(0, etc - rain)
    liters = need_mm * area_m2
    minutes = round(liters / flow_rate_lpm, 1)
    return {
        "irrigate": need_mm > 0,
        "need_mm": need_mm,
        "minutes": minutes,
        "et0": et0,
        "rain": rain
    }
