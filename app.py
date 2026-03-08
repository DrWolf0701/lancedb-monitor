import streamlit as st
import requests

st.title("測試")

# Simple test
try:
    r = requests.get("https://google.com", timeout=5)
    st.write(f"Status: {r.status_code}")
except Exception as e:
    st.write(f"Error: {e}")

st.write("Hello World!")
