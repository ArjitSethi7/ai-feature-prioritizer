import streamlit as st
import pandas as pd
import requests
import re

# --- Password Protection ---
PASSWORD = st.secrets.get("APP_PASSWORD", "")
user_password = st.text_input("🔐 Enter Access Password:", type="password")

if user_password != PASSWORD:
    st.warning("This app is private. Please enter the password to continue.")
    st.stop()

st.set_page_config(page_title="RICE Prioritizer", layout="wide")

# Sidebar info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    Prioritize your product features using the **RICE framework**:  
    - **R**each  
    - **I**mpact  
    - **C**onfidence  
    - **E**ffort

    Upload or type features → AI ranks them → See scores + explanation → Export as CSV.
    """)

st.title("🧠 AI Feature Prioritization Assistant (RICE Framework)")
st.caption("Built with 💡 OpenRouter + Streamlit | by Arjit Sethi")
st.markdown("---")

# Input mode
input_mode = st.radio("Choose how to enter features:", ["Type manually", "Upload CSV"])
features = []

if input_mode == "Type manually":
    typed_text = st.text_area("✍️ Enter one feature per line:")
    if typed_text.strip():
        features = [line.strip() for line in typed_text.split("\n") if line.strip()]
else:
    uploaded_file = st.file_uploader("📄 Upload a CSV file with a 'Feature' column", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("✅ Uploaded Features:")
        st.dataframe(df)

        if "Feature" not in df.columns:
            st.warning("⚠️ Your CSV must have a column named 'Feature'")
        else:
            features = df["Feature"].dropna().tolist()

# Spinner state
if "processing" not in st.session_state:
    st.session_state.processing = False

if features:
    prioritize_btn = st.button("🚀 Prioritize Features", disabled=st.session_state.processing)

    if prioritize_btn:
        st.session_state.processing = True

        prompt = (
            "You're an expert product manager. Prioritize the following product features using the RICE framework. "
            "For each feature, return:\n"
            "1. The feature name\n"
            "2. Its RICE score (total score)\n"
            "3. Explanation based on R, I, C, E used\n\n"
            "Format strictly as:\n"
            "Feature Name - RICE Score: <number>\nReason: <short explanation>\n\n"
            f"Features:\n{chr(10).join(features)}"
        )

        with st.spinner("🤖 Prioritizing... Please wait"):
            def query_openrouter(prompt):
                api_key = st.secrets["OPENROUTER_API_KEY"]
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "openrouter/auto",
                    "messages": [{"role": "user", "content": prompt}]
                }
                response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                         headers=headers, json=data)
                return response.json()["choices"][0]["message"]["content"]

            try:
                prioritized_text = query_openrouter(prompt)
                st.success("✅ Prioritization complete!")

                st.markdown("### 📋 Full AI Response")
                st.code(prioritized_text)

                # Parse output
                lines = prioritized_text.split("\n")
                rows = []
                current_feature = ""
                current_score = ""
                current_reason = ""

                for line in lines:
                    if " - RICE Score:" in line:
                        parts = line.split(" - RICE Score:")
                        current_feature = parts[0].strip("•-– ")
                        current_score = parts[1].strip()
                    elif line.lower().startswith("reason:"):
                        current_reason = line.split(":", 1)[1].strip()
                        rows.append((current_feature, current_score, current_reason))

                if rows:
                    st.markdown("### 🧠 RICE Score Explanation")
                    st.markdown("""
                    - **Reach**: How many users will it impact?
                    - **Impact**: How much will it move the needle?
                    - **Confidence**: How confident are we in the estimates?
                    - **Effort**: How many resources / weeks are needed?

                    The **RICE score** is calculated as:
                    `Score = (Reach × Impact × Confidence) / Effort`
                    """)

                    result_df = pd.DataFrame(rows, columns=["Feature", "RICE Score", "Reason"])
                    st.markdown("### 🔢 Prioritized Features with RICE Scores")
                    st.dataframe(result_df)

                    csv = result_df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download CSV", data=csv,
                                       file_name="prioritized_features.csv", mime="text/csv")
                else:
                    st.warning("⚠️ Could not parse RICE scores. Try rephrasing your features.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

            st.session_state.processing = False

st.markdown("---")
st.markdown("Built by [Arjit Sethi](https://www.linkedin.com/in/arjitsethi)")
