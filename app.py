import streamlit as st
import pandas as pd
import requests
import re

# --- Free trial + Password Protection Logic ---
if "used_once" not in st.session_state:
    st.session_state.used_once = True

PASSWORD = st.secrets.get("APP_PASSWORD", "")
user_password = st.session_state.get("user_password", "")

# If user has used once and hasn't authenticated, prompt for password
if st.session_state.used_once and user_password != PASSWORD:
    st.warning("\U0001f512 Trial ended. Please enter the password to continue.")
    user_password_input = st.text_input("Enter Access Password", type="password")
    if user_password_input == PASSWORD:
        st.session_state.user_password = user_password_input
        st.success("\u2705 Access granted.")
    else:
        st.stop()

st.set_page_config(page_title="RICE Prioritizer", layout="wide")
st.title("\U0001f9e0 AI Feature Prioritization Assistant (RICE Framework)")
st.caption("Built with \U0001f4a1 OpenRouter + Streamlit | by Arjit Sethi")
st.markdown("---")

# Input mode
input_mode = st.radio("Choose how to enter features:", ["Type manually", "Upload CSV"])
features = []

if input_mode == "Type manually":
    typed_text = st.text_area("\u270d\ufe0f Enter one feature per line:")
    if typed_text.strip():
        features = [line.strip() for line in typed_text.split("\n") if line.strip()]
else:
    uploaded_file = st.file_uploader("\U0001f4c4 Upload a CSV file with a 'Feature' column", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("\u2705 Uploaded Features:")
        st.dataframe(df)

        if "Feature" not in df.columns:
            st.warning("\u26a0\ufe0f Your CSV must have a column named 'Feature'")
        else:
            features = df["Feature"].dropna().tolist()

if "processing" not in st.session_state:
    st.session_state.processing = False

if features:
    prioritize_btn = st.button("\U0001f680 Prioritize Features", disabled=st.session_state.processing)

    if prioritize_btn:
        st.session_state.processing = True

        prompt = (
            "You're an expert product manager. Prioritize the following product features using the RICE framework. "
            "For each feature, return its name and estimated Reach (R), Impact (I), Confidence (C), Effort (E), and total RICE score.\n"
            "Use this format strictly:\n"
            "Feature Name (R: x, I: x, C: x, E: x)\n"
            "\nFeatures:\n" + "\n".join(features)
        )

        with st.spinner("\U0001f916 Prioritizing... Please wait"):
            def query_openrouter(prompt):
                api_key = st.secrets["OPENROUTER_API_KEY"]
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "referrer": "https://ai-feature-prioritizer.streamlit.app/"
                }
                data = {
                    "model": "openrouter/auto",
                    "messages": [{"role": "user", "content": prompt}]
                }
                response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=data)
                json_response = response.json()

                # Debug print
                st.markdown("#### 🔍 Raw API Response")
                st.code(json_response)

                if "choices" not in json_response:
                    raise Exception(f"Unexpected response: {json_response}")

                return json_response["choices"][0]["message"]["content"]

            try:
                ai_response = query_openrouter(prompt)
                st.success("\u2705 Prioritization complete!")

                # Show raw output for debugging
                st.markdown("### \U0001f9ea Raw AI Output")
                st.code(ai_response)

                def parse_rice_scores(ai_response):
                    pattern = r'^(.*?)(?:\s*\(R:\s*(\d+),\s*I:\s*(\d+),\s*C:\s*(\d+),\s*E:\s*(\d+)\))'
                    matches = re.findall(pattern, ai_response, re.MULTILINE)

                    parsed = []
                    for match in matches:
                        name = match[0].strip(" -1234567890.\n")
                        reach, impact, confidence, effort = map(int, match[1:])
                        rice_score = round((reach * impact * confidence) / (effort if effort != 0 else 1), 2)
                        parsed.append({
                            "Feature": name,
                            "RICE Score": rice_score,
                            "R": reach, "I": impact, "C": confidence, "E": effort
                        })
                    return parsed

                parsed_scores = parse_rice_scores(ai_response)

                if not parsed_scores:
                    st.warning("We couldn’t parse the AI's RICE scores. You can try rephrasing your features or copying the raw output below.")
                    st.stop()

                result_df = pd.DataFrame(parsed_scores)
                result_df = result_df.sort_values(by="RICE Score", ascending=False)

                st.markdown("### \U0001f9ea RICE Score Explanation")
                st.markdown("""
                - **Reach**: How many users will it impact?
                - **Impact**: How much will it move the needle?
                - **Confidence**: How confident are we in the estimates?
                - **Effort**: How many resources / weeks are needed?

                **RICE score** = (Reach × Impact × Confidence) / Effort
                """)

                st.markdown("### \U0001f522 Prioritized Features")
                st.dataframe(result_df[["Feature", "RICE Score"]])

                csv = result_df[["Feature", "RICE Score", "R", "I", "C", "E"]].to_csv(index=False).encode("utf-8")
                st.download_button("\U0001f4e5 Download CSV", data=csv,
                                   file_name="prioritized_features.csv", mime="text/csv")

                # Mark free trial used
                st.session_state.used_once = True

            except Exception as e:
                st.error(f"\u274c Error: {str(e)}")

            st.session_state.processing = False

st.markdown("---")
st.markdown("Made with by [Arjit Sethi](https://www.linkedin.com/in/arjitsethi)")
