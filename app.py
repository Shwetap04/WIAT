import streamlit as st
import ollama
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="💧 Weather-based Irrigation Assistant", page_icon="💧", layout="centered")

st.title("💧 Weather-based Irrigation Assistant")

# -------------------------------
# Mock weather forecast
# -------------------------------
def get_weather_forecast():
    today = datetime.now()
    return [
        {"date": (today + timedelta(days=0)).strftime("%Y-%m-%d"), "precip_mm": 0.2, "et0_mm": 4.47},
        {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "precip_mm": 1.2, "et0_mm": 3.95},
        {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "precip_mm": 0.0, "et0_mm": 5.1},
    ]

# -------------------------------
# Rule-based responses
# -------------------------------
def irrigation_rule(et0, rain):
    if rain >= et0:
        return "🌧 Rainfall is sufficient. No irrigation needed."
    elif rain >= 0.5 * et0:
        return "💧 Rainfall covered ~50% of crop need. Apply light irrigation."
    else:
        return "⚠️ Rainfall insufficient. Full irrigation recommended."

def rule_based_response(prompt: str):
    text = prompt.lower().strip()

    # Greetings
    if text in ["hi", "hello", "hey", "hii", "good morning", "good evening"]:
        return "👋 Hello! How can I help you with irrigation or weather today?"

    # Small talk
    if "how are you" in text:
        return "😊 I'm doing great! Ready to help you with irrigation and weather advice."

    # Irrigation decision
    if "et0" in text and "rain" in text:
        et0_match = re.search(r"et0\s*=?\s*([\d.]+)", text)
        rain_match = re.search(r"rain\s*=?\s*([\d.]+)", text)
        if et0_match and rain_match:
            et0 = float(et0_match.group(1))
            rain = float(rain_match.group(1))
            return irrigation_rule(et0, rain)

    # Weather forecast (but not when asking about crops/strawberries)
    if ("weather" in text or "forecast" in text) and not ("strawberry" in text or "crop" in text):
        forecast = get_weather_forecast()
        return "🌦 Weather forecast:\n" + "\n".join(
            [f"{f['date']}: rain={f['precip_mm']}mm, ET₀={f['et0_mm']}mm" for f in forecast]
        )

    # Rain tomorrow
    if "rain tomorrow" in text:
        forecast = get_weather_forecast()
        return f"🌧 Rain expected tomorrow: {forecast[1]['precip_mm']}mm"

    # Rain in last 3 days
    if "last 3 days rain" in text:
        total = sum([f["precip_mm"] for f in get_weather_forecast()])
        return f"🌧 Total rain in last 3 days: {total}mm"

    # Irrigation after rain
    if "irrigate after rain" in text:
        return "💡 Wait 1–2 days after heavy rain before irrigating, unless soil dries quickly."

    # Best time to irrigate
    if "best time" in text and "irrigate" in text:
        return "⏰ Best irrigation time is early morning or late evening to reduce evaporation."

    # Crop-specific water need
    if "which crop needs more water" in text:
        return "🌱 Paddy needs the most water now, while wheat requires moderate irrigation."

    # Hours for wheat/paddy
    if "how many hours" in text and "wheat" in text:
        return "🌾 Wheat usually requires ~2–3 hours of irrigation per acre depending on soil."
    if "how many hours" in text and "paddy" in text:
        return "🌾 Paddy requires ~4–6 hours of irrigation per acre depending on water depth."

    # Irrigation method
    if "drip or flood" in text:
        return "💧 Drip is more water-efficient, but flood may be used for paddy fields."

    # Warning about drought
    if "drought" in text or "shortage" in text:
        return "⚠️ Warning: Low rainfall this week, conserve water and use efficient irrigation."

    # If no rule matches → None
    return None

# -------------------------------
# Session state for chat
# -------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "👋 Hello! Ask me about irrigation, weather, or crops."}
    ]

# Display history
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).markdown(msg["content"])

# -------------------------------
# Chat input
# -------------------------------
if prompt := st.chat_input("Ask about irrigation, weather, or crops..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # Rule-based reply first
    reply = rule_based_response(prompt)

    # Fallback to Ollama
    if reply is None:
        try:
            with st.spinner("Thinking..."):
                stream = ollama.chat(
                    model="mistral",
                    messages=st.session_state["messages"],
                    stream=True
                )
                reply = ""
                placeholder = st.chat_message("assistant").markdown("")

                for chunk in stream:
                    token = chunk["message"]["content"]
                    reply += token
                    placeholder.markdown(reply)

        except Exception as e:
            reply = f"⚠️ Error: {str(e)}"

    else:
        # Rule-based response shown here
        st.chat_message("assistant").markdown(reply)

    # Save reply in history
    st.session_state["messages"].append({"role": "assistant", "content": reply})
