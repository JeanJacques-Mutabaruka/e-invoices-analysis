import google.generativeai as genai
import streamlit as st

# If you're using Streamlit secrets:
# api_key = st.secrets["google"]["GEMINI_API_KEY"]

# Otherwise, paste your key directly here for testing

api_key = st.secrets["google"]["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# List all models available to your key
models = genai.list_models()
print("\n✅ Available Gemini models for your API key:\n")
for m in models:
    print(f"• {m.name}  (supports: {getattr(m, 'supported_generation_methods', 'N/A')})")
