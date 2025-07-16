import streamlit as st
import pandas as pd
import requests
import re

# --- Session and Password Protection ---
if "used_once" not in st.session_state:
    st.session_state.used_once = False

PASSWORD = st.secrets.get("APP_PASSWORD", "")
user_password = st.session_state.get("user_password", "")

# Require password after first use
if st.session_state.used_once and user_password != PASSWORD:
    st.warning("🔒 Trial ended. Please enter the password to continue.")
    user_password_input = st.text_input("Enter Access Password", type="password")
    if user_password_input == PASSWORD:
        st.session_state.user_password = user_password_input
        st.success("✅ Access granted.")
    else:
        st.stop()

# --- App Title ---
st.title("🔍 AI Feature Prioritization Assistant")

# --- Input Method ---
input_method = st.radio("Choose input method:", ["Type Features", "Upload CSV"])
features = []

if input_method == "Type Features":
    features_text = st.text_area("Enter one feature per line:")
    if features_text:
        features = features_text.strip().split("\n")
else:
    uploaded_file = st.file_uploader("Upload a CSV with a column named 'Feature'", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "Feature" in df.columns:
            features = df["Feature"].dropna().tolist()
        else:
            st.error("CSV must have a column named 'Feature'.")

# --- Process Features ---
if features:
    if st.button("🚀 Prioritize"):
        with st.spinner("Prioritizing features using AI..."):
            prompt = (
                "Prioritize these product features using the RICE framework (Reach, Impact, Confidence, Effort). "
                "For each, assign a RICE score (R × I × C ÷ E), explain the reasoning, and format output as:\n\n"
                "Feature Name - RICE Score (R: _, I: _, C: _, E: _)\nExplanation:\n...\n\n"
                "Features:\n" + "\n".join(features)
            )

            headers = {
                "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
            }

            data = {
                "model": "openrouter/auto",
                "messages": [{"role": "user", "content": prompt}],
            }

            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                output = response.json()["choices"][0]["message"]["content"]
                st.session_state.used_once = True  # Mark free trial as used

                # Parse and display results
                matches = re.findall(
                    r"(?P<feature>.+?)\s*[-:–]\s*RICE\s*Score\s*[:\-]?\s*(?P<score>\d+).*?R\s*[:\-]?\s*(\d).*?I\s*[:\-]?\s*(\d).*?C\s*[:\-]?\s*(\d).*?E\s*[:\-]?\s*(\d)",
                    output,
                    re.DOTALL | re.IGNORECASE,
                )

                explanations = re.findall(r"Explanation\s*[:\-]?\s*(.*?)(?=\n\S|$)", output, re.DOTALL)

                if matches:
                    result_df = pd.DataFrame([
                        {
                            "Feature": m[0].strip(),
                            "RICE Score": int(m[1]),
                            "Reason": explanations[idx].strip() if idx < len(explanations) else ""
                        }
                        for idx, m in enumerate(matches)
                    ])
                    st.subheader("📋 Prioritized Features")
                    st.dataframe(result_df)

                    csv = result_df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download CSV", data=csv, file_name="prioritized_features.csv", mime="text/csv")
                else:
                    st.warning("⚠️ We couldn’t parse the AI's RICE scores. You can try rephrasing your features or copying the raw output below.")
                    st.text_area("Raw AI Output", value=output, height=300)
                    st.stop()

            except Exception as e:
                st.error(f"Error: {e}")
