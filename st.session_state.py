import streamlit as st
from llm_handler import ask_groq  # assuming you call Groq here

st.title("Argo Float Query")

if "last_response" not in st.session_state:
    st.session_state.last_response = None

query = st.text_input("Enter your question:")
if st.button("Ask"):
    with st.spinner("Querying Groq..."):
        response = ask_groq(query)
        st.session_state.last_response = response

if st.session_state.last_response:
    st.write("✅ Groq response received successfully")
    st.json(st.session_state.last_response)
