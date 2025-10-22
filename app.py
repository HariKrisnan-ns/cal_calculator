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


def preprocess_image(image):
    # Convert to RGB (avoid alpha channel issues)
    image = image.convert("RGB")
    # Resize to max 512x512 (you can tune this size)
    image = image.resize((512, 512))
    return image


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
    try:
        original_image = Image.open(uploaded_file)
        image = preprocess_image(original_image)
        st.image(original_image, caption="Uploaded Image", use_column_width=True)
    except Exception as e:
        st.error(f"Error displaying image: {e}")




submit = st.button("Tell me about the total calories")

input_prompt = """
You are a certified nutritionist and expert in food image analysis.

Please analyze the uploaded image of a meal and provide a detailed nutritional breakdown. Your task is to:

1️⃣ **Identify each visible food item** (e.g., rice, dal, chapati, curry, boiled egg, salad).  
2️⃣ For each item, provide:
   - Estimated **calories (kcal)**  
   - Approximate **protein (g)**  
   - Optionally mention **carbs or fats** if visually identifiable  
3️⃣ Calculate the **total calories and total protein** for the whole meal.  
4️⃣ Provide a brief 🩺 **Health Summary** — is the meal high/low in calories, protein-rich, balanced, or needs improvement?  
5️⃣ Finally, give 1–2 lines of 🎯 **Professional Advice** that is specific, practical, and encouraging. This can include:
   - What to add/remove
   - Notes for fitness or weight goals
   - Tips on balance, hydration, fiber, etc.

📋 Format your response like this:

🍽️ **Meal Breakdown**  
1. Rice (1 cup) — Approx. 205 kcal, 4g protein  
2. Dal (1 cup) — Approx. 180 kcal, 9g protein  
3. Boiled Egg — Approx. 78 kcal, 6g protein  
...

🔢 **Total** — 463 kcal, 19g protein  

🩺 **Health Summary**: A protein-rich, moderate-calorie meal with good balance of carbs and fiber.

💡 **Professional Advice**:  
✅ Great choice! Add a small bowl of curd or salad for gut health.  
🏋️‍♂️ If you're targeting muscle gain, consider adding paneer or legumes for more protein.  
💧 Stay hydrated and try to avoid fried sides regularly.

⚠️ Ignore cutlery, plates, or background objects. Only focus on the actual food items visible.
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
