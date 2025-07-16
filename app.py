import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="RICE Prioritizer", layout="wide")

# Sidebar info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This AI assistant helps prioritize features using the **RICE framework**:
    - **Reach**
    - **Impact**
    - **Confidence**
    - **Effort**

    Upload or type features → AI ranks them → Download results.
    Built with 🧠 AI via OpenRouter & Streamlit.
    """)

st.title("🧠 AI Feature Prioritization Assistant (RICE Framework)")
st.caption("Made with 💡 OpenRouter + Streamlit | by Arjit Sethi")
st.markdown("---")

# Input/output tabs
tab1, tab2 = st.tabs(["📝 Input Features", "📋 Prioritized Output"])

features = []

with tab1:
    input_mode = st.radio("Choose how to enter features:", ["Type manually", "Upload CSV"])

    if input_mode == "Type manually":
        typed_text = st.text_area("Enter one feature per line:")
        if typed_text.strip():
            features = [line.strip() for line in typed_text.split("\n") if line.strip()]
    else:
        uploaded_file = st.file_uploader("Upload CSV with a 'Feature' column", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("📄 Uploaded Features:")
            st.dataframe(df)

            if "Feature" not in df.columns:
                st.warning("⚠️ CSV must have a column named 'Feature'")
            else:
                features = df["Feature"].dropna().tolist()

# Session state to handle spinner lock
if "processing" not in st.session_state:
    st.session_state.processing = False

with tab2:
    if features:
        prioritize_btn = st.button("🚀 Prioritize Features", disabled=st.session_state.processing)

        if prioritize_btn:
            st.session_state.processing = True

            prompt = "Prioritize the following features using the RICE framework. " \
                     "Only return one line per feature in the format: Feature Name - Score (R: X, I: X, C: X, E: X). " \
                     "Sort them in descending RICE score. No explanations.\n\n" + "\n".join(features)

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
                    st.markdown("### 🔢 Prioritized Features with RICE Scores")
                    st.write(prioritized_text)

                    lines = prioritized_text.split("\n")
                    rows = []
                    for line in lines:
                        match = re.match(r"^(.*?)-\s*(\d+)(\s|\(R:)", line.strip())
                        if match:
                            feature = match.group(1).strip("•-– ")
                            score = match.group(2)
                            rows.append((feature, score))

                    if rows:
                        result_df = pd.DataFrame(rows, columns=["Feature", "RICE Score"])
                        st.dataframe(result_df)

                        csv = result_df.to_csv(index=False).encode("utf-8")
                        st.download_button("📥 Download CSV", data=csv,
                                           file_name="prioritized_features.csv", mime="text/csv")
                    else:
                        st.warning("⚠️ Could not parse RICE scores properly. Try rephrasing your features.")

                except Exception as e:
                    st.error(f"Something went wrong: {str(e)}")

                st.session_state.processing = False

st.markdown("---")
st.markdown("Built by [Arjit Sethi](https://www.linkedin.com/in/arjit-sethi/)")
