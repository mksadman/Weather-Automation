import streamlit as st
import pandas as pd

EXCEL_FILE = "weather_report.xlsx"
df = pd.read_excel(EXCEL_FILE)


st.title("🌤️ Weather Dashboard")


cities = df["City"].unique()
selected_city = st.selectbox("Select a City", cities)


city_data = df[df["City"] == selected_city]


st.write("### Weather Data", city_data)


st.line_chart(city_data.set_index("Date")[["Max Temperature (°C)", "Min Temperature (°C)"]])

st.write("📊 Data is updated daily. Stay tuned!")

