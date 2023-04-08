import streamlit as st

def dashboard_app():
    st.title('Hello world!')

    for i in range(10):
        st.write(f"This is Profiler number {i}")