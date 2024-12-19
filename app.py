import streamlit as st
from utils import multi_lingual_stream_brochure

def main():
    st.title("Company Brochure Generator")

    company_name = st.text_input("Company Name", value="OpenAI")
    url = st.text_input("Company URL", value="https://openai.com/")
    language = st.selectbox("Choose Language", ["English",  "Marathi", "Urdu", "French", "Spanish", "German", "Hindi", "Korea", "Japanese", "Chinese"])
    tone = st.selectbox("Choose Tone", ["Formal", "Casual", "Professional", "Inspirational", "humorous, entertaining, jokey"])

    if st.button("Generate Brochure"):
        with st.spinner("Generating brochure..."):
            multi_lingual_stream_brochure(company_name, url, language, tone)


if __name__ == "__main__":
    main()
