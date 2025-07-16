import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = st.secrets["OPENROUTER_API_KEY"]

st.write("🔐 API key loaded:", api_key[:8] + "...")

st.title("🧠 Free AI Feature Prioritizer (OpenRouter)")

features_input = st.text_area("Enter one product feature per line:")
framework = st.selectbox("Select framework", ["RICE"])

def query_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://openrouter.ai",  # Required for free tier
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",  # You can change model here
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    return response.json()

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
