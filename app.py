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
        "Referer": "https://arjit7-rice-ai-prioritizer.streamlit.app"
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
        with st.spinner("🧠 Thinking... Prioritizing with RICE..."):

            if input_mode == "📤 Upload CSV":
                prompt = (
                    "You are a product manager. Prioritize the following features using the RICE framework. "
                    "Return the result as a table with columns: Feature, Reason (based on RICE), and keep any other original metadata. "
                    "Format the response in markdown table style. Here are the features with metadata:\n\n"
                    + df.to_csv(index=False)
                )
            else:
                prompt = (
                    "You are a product manager. Prioritize the following features using the RICE framework. "
                    "Return a markdown table with columns: Feature and Reason (based on RICE). Here are the features:\n\n"
                    + "\n".join(features)
                )

            prioritized_text = query_openrouter(prompt)

        st.subheader("🔢 Prioritized Table:")
        st.markdown(prioritized_text)

        # --- Parse markdown to DataFrame ---
        try:
            result_df = pd.read_csv(pd.compat.StringIO(
                "\n".join([line for line in prioritized_text.split('\n') if '|' in line and not line.strip().startswith('|---')])
            ), sep="|", engine="python").dropna(axis=1, how='all')

            result_df.columns = result_df.columns.str.strip()
            result_df = result_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            st.dataframe(result_df)

            # --- Enable CSV download ---
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Prioritized CSV", data=csv, file_name="prioritized_features.csv", mime="text/csv")

        except Exception as e:
            st.error("⚠️ Could not parse the table. Please copy manually:")
            st.code(prioritized_text)
