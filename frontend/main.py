# === frontend/main.py ===
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/ask"  # Ensure FastAPI runs here

st.set_page_config(page_title="Legal AI Chatbot", page_icon="⚖️")
st.title("📚 Legal AI Chatbot for Indian Law")
st.markdown("Ask any question related to Indian law and get a legal answer backed by real law data.")

# Input area
user_question = st.text_input("Your Legal Question:", placeholder="e.g., What does Section 2 define in the Income Tax Act?")

if st.button("Get Answer") and user_question:
    with st.spinner("Getting answer from Legal Bot..."):
        try:
            response = requests.post(API_URL, json={"question": user_question})
            if response.status_code == 200:
                st.success("Answer:")
                st.write(response.json()["response"])
            else:
                st.error("Error from backend. Please check server logs.")
        except Exception as e:
            st.error("Connection error. Is the backend running?")

# Optional: Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and Gemini")