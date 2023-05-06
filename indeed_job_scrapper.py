from bs4 import BeautifulSoup
import cloudscraper
from random import random
from time import sleep
from email.message import EmailMessage
from collections import namedtuple
import smtplib
import csv
import re

EmailCredentials = namedtuple("EmailCredentials", ['username', 'password', 'sender', 'recipient'])
scraper = cloudscraper.create_scraper()

def generate_url(job_title, job_location):
    url_template = "https://ca.indeed.com/jobs?q={}&l={}"
    url = url_template.format(job_title, job_location)
    return url


def save_record_to_csv(record, filepath, create_new_file=False):
    """Save an individual record to file; set `new_file` flag to `True` to generate new file"""
    header = ["JobTitle", "Company", "Location", "Salary", "PostDate", "Summary", "JobUrl"]
    if create_new_file:
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
    else:
        with open(filepath, mode='a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(record)


def email_jobs_file(filepath, email):
    """This is currently setup for GMAIL. However, you may need to enable `less secure apps` for
    your email account if you want this to work. See: https://support.google.com/accounts/answer/6010255?hl=en"""
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    with smtplib.SMTP(host=smtp_host, port=smtp_port) as server:
        server.starttls()
        server.login(email.username, email.password)
        message = EmailMessage()
        message['From'] = email.sender
        message['To'] = email.recipient
        message['Subject'] = "Updated jobs file"
        message['Body'] = "The updated Indeed postings are attached."
        message.add_attachment(open(filepath, 'r').read(), filename="indeed.csv")
        server.send_message(message)


def collect_job_cards_from_page(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    cards = soup.find_all('div', 'job_seen_beacon')
    return cards, soup


def find_next_page(soup):
    try:
        pagination = soup.find("a", {"aria-label": "Next Page"}).get("href")
        print("NEXT PAGE")
        return "https://ca.indeed.com" + pagination
    except AttributeError:
        return None


def extract_job_card_data(card):
    atag = card.h2.a
    try:
        job_title = card.find('h2','jobTitle').text
    except AttributeError:
        job_title = ''
    try:
        company = card.find('span','companyName').text
    except AttributeError:
        company = ''
    try:
        location = card.find('div','companyLocation').text
    except AttributeError:
        location = ''
    try:
        post_date = card.find('span', 'date').text.strip()
    except AttributeError:
        post_date = ''

    job_url = 'https://ca.indeed.com' + atag.get('href')
    return job_title, company, location, post_date, job_url


def main(job_title, job_location, filepath, email=None):
    unique_jobs = set()  # track job urls to avoid collecting duplicate records
    print("Starting to scrape indeed for `{}` in `{}`".format(job_title, job_location))
    url = generate_url(job_title, job_location)
    save_record_to_csv(None, filepath, create_new_file=True)
    
    while True:
        print(url)
        html = scraper.get(url)
        if not html:
            break
        cards, soup = collect_job_cards_from_page(html)
        soup.find('div','css-tvvxwd')
        for card in cards:
            record = extract_job_card_data(card)
            if not record[-1] in unique_jobs:
                save_record_to_csv(record, filepath)
                unique_jobs.add(record[-1])
        url = find_next_page(soup)
        if not url:
            break
    print('Finished collecting {:,d} job postings.'.format(len(unique_jobs)))
    if email:
        email_jobs_file(filepath, email)


if __name__ == '__main__':
    # job search settings
    title = 'Software Developer'
    loc = 'Vancouver'
    path = 'indeed_job.csv'

    # without email settings
    main(title, loc, path)