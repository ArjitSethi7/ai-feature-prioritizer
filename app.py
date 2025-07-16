import streamlit as st
import pandas as pd
import requests

# --- Load OpenRouter API key ---
api_key = st.secrets["OPENROUTER_API_KEY"]

# --- Query OpenRouter function ---
def query_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Referer": "https://ai-feature-prioritizer.streamlit.app/"
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
        st.error(f"⚠️ OpenRouter error: {response.text}")
        return "Error: could not fetch response."


# --- Streamlit UI ---
st.set_page_config(page_title="AI RICE Prioritizer", layout="centered")
st.title("🧠 AI Feature Prioritization Assistant (RICE Framework)")
st.write("Prioritize your product features using the RICE framework with AI.")

# --- Input mode selection ---
input_mode = st.radio("Choose how to enter your features:", ["📝 Type manually", "📤 Upload CSV"])

features = []

# --- Manual input mode ---
if input_mode == "📝 Type manually":
    typed_text = st.text_area("Enter one feature per line:")
    if typed_text.strip():
        features = [line.strip() for line in typed_text.split("\n") if line.strip()]

# --- CSV upload mode ---
else:
    uploaded_file = st.file_uploader("Upload a CSV file with a 'Feature' column", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("📄 Uploaded Features:")
        st.dataframe(df)

        if "Feature" not in df.columns:
            st.warning("⚠️ Please make sure your CSV has a column named **'Feature'**.")
        else:
            features = df["Feature"].dropna().tolist()

# --- Run prioritization ---
if features:
    if st.button("🚀 Prioritize Features"):
        prompt = "Prioritize the following features using the RICE framework:\n" + "\n".join(features)
        prioritized_text = query_openrouter(prompt)

        st.subheader("🔢 Prioritized List:")
        st.write(prioritized_text)

        # --- Convert and allow CSV export ---
        lines = [line.strip("•- ") for line in prioritized_text.split("\n") if line.strip()]
        result_df = pd.DataFrame(lines, columns=["Prioritized Feature"])
        csv = result_df.to_csv(index=False).encode("utf-8")

        st.download_button("📥 Download as CSV", data=csv, file_name="prioritized_features.csv", mime="text/csv")
