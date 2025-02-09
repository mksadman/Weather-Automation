import requests
import pandas as pd
import schedule
import time
import streamlit as st
import smtplib
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

API_URL = "https://api.open-meteo.com/v1/forecast"
CITIES = {
    "Dhaka": (23.8103, 90.4125),
    "New York": (40.7128, -74.0060),
    "London": (51.5074, -0.1278)
}
EXCEL_FILE = "weather_report.xlsx"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SERVICE_ACCOUNT_FILE = "your_service_account.json"  # <-- Add your JSON file here

EMAIL_SENDER = "sadmankhan334@gmail.com"
EMAIL_RECEIVER = "zinniafc@gmail.com"
EMAIL_PASSWORD = "zkrr mqjr bzbn ngle"

def fetch_weather(city, lat, lon):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto"
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        return pd.DataFrame({
            "City": city,
            "Date": data["daily"]["time"],
            "Max Temperature (°C)": data["daily"]["temperature_2m_max"],
            "Min Temperature (°C)": data["daily"]["temperature_2m_min"]
        })
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {city}: {e}")
        return None


def upload_to_drive(file_path, folder_id=None):
    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        drive_service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": file_path.split("/")[-1]}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(file_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        print(f"File uploaded successfully! File ID: {file.get('id')}")
    except Exception as e:
        print(f"Error uploading file: {e}")


def send_email(file_path):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Daily Weather Report"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg.set_content("Attached is today's weather report.")

        with open(file_path, "rb") as file:
            msg.add_attachment(file.read(), maintype="application", subtype="octet-stream", filename=file_path)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


def main():
    print("Fetching weather data for multiple cities...")
    
    all_weather_data = [fetch_weather(city, lat, lon) for city, (lat, lon) in CITIES.items()]
    df = pd.concat([data for data in all_weather_data if data is not None], ignore_index=True)

    if df.empty:
        print("No data fetched. Exiting program.")
        return

    df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
    print("Weather report saved successfully!")

    send_email(EXCEL_FILE)

    upload_to_drive(EXCEL_FILE)

# Schedule Daily Execution
# schedule.every().day.at("07.00").do(main)

if __name__ == "__main__":
    main()
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
