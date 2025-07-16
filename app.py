import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = st.secrets["OPENROUTER_API_KEY"]

st.title("🧠 Free AI Feature Prioritizer (OpenRouter)")

features_input = st.text_area("Enter one product feature per line:")
framework = st.selectbox("Select framework", ["RICE"])

def query_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Referer": "https://ai-feature-priotitizer-bhvtjkhnqpvyc3lsebny2b.streamlit.app"  # MUST match your Streamlit app domain
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    try:
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error("⚠️ OpenRouter error: " + str(response.text))
        return "Error: could not fetch response."

if st.button("Prioritize"):
    if not features_input.strip():
        st.warning("Please enter at least one feature.")
    else:
        prompt = f"""
You are a product manager. Use the {framework} framework (Reach, Impact, Confidence, Effort) to prioritize the following product features:

{features_input}

Provide scores and reasoning in this format:
1. Feature name - RICE Score - (Reach: X, Impact: Y, Confidence: Z, Effort: W)
"""
        with st.spinner("Getting AI response..."):
            result = query_openrouter(prompt)
            try:
                content = result["choices"][0]["message"]["content"]
            except:
                content = str(result)
            st.markdown("### 🔽 Prioritized List:")
            st.text(content)
