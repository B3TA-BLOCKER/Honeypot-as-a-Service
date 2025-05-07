from flask import Flask, request
import csv
import os
from datetime import datetime

app = Flask(__name__)

log_file = "/opt/haas/logs/recon_data.csv"

@app.route("/")
def home():
    user_agent = request.headers.get('User-Agent')
    ip_address = request.remote_addr
    referer = request.headers.get('Referer')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get geolocation data (this will be a mock for now)
    location_data = "Mock Location Data"

    # Log data to CSV
    with open(log_file, mode='a') as log:
        log_writer = csv.writer(log)
        log_writer.writerow([timestamp, ip_address, location_data, user_agent, referer])

    return "Welcome to the fake admin panel!"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
