from PIL import Image
import streamlit as st
import base64
import io
import os
import requests
from dotenv import load_dotenv
load_dotenv()

# Try Streamlit secret first; fallback to .env for local
api_key = st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY"))

if not api_key:
    st.error("API Key not found. Please add it to `.env` or Streamlit Secrets.")


# BACKEND


def image_to_base64(image):  # fn to convert image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to call Claude 3 via OpenRouter


def get_calorie_estimate_with_openrouter(image_base64, prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://calcalculator-harikrishnan.streamlit.app/",
        "Content-Type": "application/json"
    }

    data = {
        "model": "anthropic/claude-3-haiku:beta",  # Claude 3 vision model
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# FRONTEND SETUP

st.set_page_config(page_title="Calories Adviser App")
st.header("🍱 Calories Adviser App")


uploaded_file = st.file_uploader("Upload an image", type=[
                                 "png", "jpg", "jpeg"], key="uploader")
image = None


if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)


submit = st.button("Tell me about the total calories")

input_prompt = """
You are a certified nutritionist specializing in food image analysis.

Please analyze the following image of a meal. Your task is to:
1. Identify and name each visible food item (e.g., rice, curry, chapati, salad).
2. Estimate the number of calories for each item based on common Indian serving sizes.
3. Calculate the total calorie count for the entire meal.
4. At the end, briefly state whether this meal is high/low in calories, balanced, or needs improvement.

🧾 Format your answer as:
1. Item Name — Approx. X calories
2. Item Name — Approx. Y calories
...
Total — Z calories

📋 Example:
1. 2 Chapatis — Approx. 260 calories
2. Dal (1 cup) — Approx. 180 calories
3. Boiled Egg — Approx. 78 calories
4. Cucumber Salad — Approx. 20 calories
Total — 538 calories

Include only relevant food items and ignore background objects or cutlery.
Be concise, clear, and professional.
"""

# Process if user clicks the button
if submit:
    if image is not None:
        with st.spinner("Analyzing the image..."):
            try:
                img_b64 = image_to_base64(image)
                result = get_calorie_estimate_with_openrouter(
                    img_b64, input_prompt)
                st.subheader("🍎 Calories Breakdown:")
                st.write(result)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.error("Please upload an image first.")


col1, col2 = st.columns(2)


with col1:
    if st.button("🔄 Reset"):
        if "uploader" in st.session_state:
            del st.session_state["uploader"]
        st.rerun()


with col2:
    if st.button("❌ Exit Info"):
        st.info("To close the app, press Ctrl+C in terminal or close this browser tab.")
