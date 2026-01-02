import streamlit as st
from streamlit_folium import st_folium
import folium

st.title("Minimal Folium Test")

try:
    m = folium.Map(location=[-5.58, 105.38], zoom_start=15)
    folium.Marker([-5.58, 105.38], popup="Test").add_to(m)
    
    st.write("Rendering map below...")
    st_folium(m, width=700, height=500)
    st.write("Map rendered.")
except Exception as e:
    st.error(f"Error: {e}")
