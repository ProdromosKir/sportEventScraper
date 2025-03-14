


import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import pandas as pd
import os 

from helpers import *
import Event

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


import smtplib, ssl
from dotenv import load_dotenv
import os

import re
from flask import Flask,render_template,send_from_directory

from webdriver_manager.chrome import ChromeDriverManager




load_dotenv()
app = Flask(__name__)

# Set the folder where images are stored
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'channel_logos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to serve images from the custom folder
@app.route('/channel_logos/<filename>')
def upload_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def download_image(url, folder='static/channel_logos'):
    image_name = url.split('/')[-1]

    # Check if image already exists
    if image_name in os.listdir(folder):
        return folder + '/' + image_name

    saved_path = os.path.join(folder, image_name)
    response = requests.get(url)
    if response.status_code == 200:
        with open(saved_path, 'wb') as f:
            f.write(response.content)

    return saved_path 

def find_channel_name(channel_url):
    channel_name = channel_url.split('/')[-1].split('.')[0]
    return channel_name

def fix_channel_name(incorrect_name):
    # Match Cosmote Sports channels with _6 format
    if re.match(r'^cosmotesports_\d+$', incorrect_name.lower()):
        return 'Cosmote Sports ' + incorrect_name[-1]
    
    # Match Nova Sports channels with 6a, 1a, 2a, etc.
    if re.match(r'^novasports\d*a$', incorrect_name.lower()):
        # Remove the "a" at the end and get the numeric part
        number = re.sub(r'\D', '', incorrect_name)
        return 'Nova Sports ' + number

    return incorrect_name

def fix_participant_format(participants):
    return participants.replace('\n', ' ').replace(' - ', ' - ')

def remove_static_prefix(image_path):
    # Define the static path to remove (just the "static/" part)
    static_prefix = 'static/'

    # Check if the image path starts with "static/"
    if image_path.startswith(static_prefix):
        # Remove the "static/" prefix and return the rest of the path
        return image_path[len(static_prefix):]
    
    return image_path  # If the static prefix isn't in the image path, return it as is


CHANNEL_LOGOS_FOLDER = os.path.join(os.getcwd(), 'channel_logos')
app.config['CHANNEL_LOGOS_FOLDER'] = CHANNEL_LOGOS_FOLDER

# Configure Flask app with SERVER_NAME
app.config['SERVER_NAME'] = 'localhost:5000'  # Set it to your actual domain if you have one
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'http'

# Route to send images from 'channel_logos'
@app.route('/logos/<filename>')
def send_logo(filename):
    return send_from_directory(app.config['CHANNEL_LOGOS_FOLDER'], filename)

@app.route('/')
def scrape():
    url = 'https://www.gazzetta.gr/tv-program'

    chromedriver_path = 'chromedriver-mac-arm64/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('--no-headless')
    options.add_argument('--no-sandbox')

    service = Service(ChromeDriverManager().install())
    
    #driver = webdriver.Chrome(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    scrapped_events = []

    tv_schedule = driver.find_element(By.CLASS_NAME, 'tv_schedule_wrapper')
    events = tv_schedule.find_elements(By.CLASS_NAME, 'list-item')

    for event in events:
        e = Event.Event()
        e.time = event.find_element(By.CLASS_NAME, 'list-item__time-area').text
        e.channel_div = event.find_element(By.CLASS_NAME, 'channel_div')
        e.channel = e.channel_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
        
        # Download the image and save the path
        e.image_path = download_image(e.channel)

        e.image_path = remove_static_prefix(e.image_path)

        e.channel_name = find_channel_name(e.channel)
        e.channel = fix_channel_name(e.channel_name)

        e.participants = event.find_element(By.CLASS_NAME, 'participant').text
        e.participants = fix_participant_format(e.participants)

        e.competition = event.find_element(By.CLASS_NAME, 'fixture__competition').text

        scrapped_events.append(e)

    driver.quit()

    write_events_to_txt(scrapped_events)
    read_events_from_txt('events.txt')
    send_mail(scrapped_events)

    # You can choose to return these scraped events as JSON or render them on a template
    # For now, returning them as a simple response:
    return scrapped_events

def write_events_to_txt(scrapped_events):   
    with open('events.txt', 'w') as f:
        for e in scrapped_events:
            f.write(repr(e) + '\n')

def read_events_from_txt(filename):
    with open(filename, 'r') as f:
        return f.read()








def send_mail(scrapped_events):
        # Your credentials
    sender_email = "sendtvprogram@gmail.com"
    receiver_email = "prodrkir@gmail.com"
    app_password = os.getenv("APP_PASSWORD") # The app-specific password generated by Google

    # SMTP server details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Create the message
    subject = "Today's TV Program Schedule - Gazzetta.gr"
    # Set up the MIME (Multipurpose Internet Mail Extensions) for the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject



    with app.app_context():
        body = render_template('email_template.html', events=scrapped_events)
    #message.attach(MIMEText(body, "plain"))
    message.attach(MIMEText(body, "html"))

    try:
        # Set up the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Start TLS encryption
            server.login(sender_email, app_password)  # Log in with your email and app-specific password
            server.sendmail(sender_email, receiver_email, message.as_string())  # Send the email
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':

    scrapped_events = scrape()  # Scrape the events
    # send_mail(scrapped_events)  # Send the scrapped events via email
    app.run(debug=True)



#send_mail()
#driver.quit()

# if __name__ == '__main__':
#     app.run(debug=True)
#     scrape()
#     write_events_to_txt(scrapped_events)
#     read_events_from_txt('events.txt')

    



