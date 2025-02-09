import requests
import pandas as pd
import schedule
import time
import logging
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

API_URL = "https://api.open-meteo.com/v1/forecast"
CITIES = {
    "Dhaka": (23.8103, 90.4125),
    "New York": (40.7128, -74.0060),
    "London": (51.5074, -0.1278)
}
EXCEL_FILE = "weather_report.xlsx"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SERVICE_ACCOUNT_FILE = "your_service_account.json"

def fetch_weather(city, lat, lon):
    try:
        logging.info(f"Fetching weather data for {city}")
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
        logging.error(f"Error fetching data for {city}: {e}")
        return None

def upload_to_drive(file_path, folder_id=None):
    try:
        logging.info("Initiating Google Drive upload")
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        drive_service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": file_path.split("/")[-1]}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(
            file_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        logging.info(f"File uploaded successfully! File ID: {file.get('id')}")
    except Exception as e:
        logging.error(f"Error uploading file: {e}")

def main():
    try:
        logging.info("Starting weather data collection")
        
        all_weather_data = [
            fetch_weather(city, lat, lon) 
            for city, (lat, lon) in CITIES.items()
        ]
        df = pd.concat(
            [data for data in all_weather_data if data is not None],
            ignore_index=True
        )

        if df.empty:
            logging.error("No data fetched. Exiting program.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_report_{timestamp}.xlsx"
        
        df.to_excel(filename, index=False, engine="openpyxl")
        logging.info(f"Weather report saved successfully as {filename}")

        upload_to_drive(filename)
        
        return True
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        return False

def run_scheduler():
    logging.info("Starting weather report scheduler")
    
    schedule.every().day.at("07:00").do(main)
    
    next_run = schedule.next_run()
    logging.info(f"Next weather report scheduled for: {next_run}")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")

if __name__ == "__main__":
    should_run_immediately = True  # Set to False for scheduled runs
    
    if should_run_immediately:
        logging.info("Running initial weather report")
        main()
    
    run_scheduler()

