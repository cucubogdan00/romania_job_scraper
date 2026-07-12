import requests
import hashlib
import csv
import time
import sqlite3

from parser import JobParser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime

class EJobsScraper:
        
    def create_job_blueprint(self):
    
        job_structure = {
            'id': None,              # Will hold the SHA-256 unique hash
            'title': "",             # Will hold the job title string
            'company': "",           # Will hold the company name string
            'location': "", 
            'experience' : "",         # Will hold the city / remote status
            'link': "",              # Will hold the URL to the job application
            'technologies': []       # Will hold a list of required skills/tech
        }
        
        return job_structure

    def fetch_html_content(self, url):

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-gpu')

        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)

            time.sleep(3)

            for i in range(7):
                current_pixel = (i + 1) * 1500
                driver.execute_script(f'window.scrollTo(0, {current_pixel});')
                print(f'      [Selenium] Incremental scroll to {current_pixel}px ({i+1}/7)...')

                time.sleep(1.5)
            
            full_html = driver.page_source

            driver.quit()

            return full_html

        except Exception as error:
            print(f'Selenium Automation Error: {error}')
            return None
        
    def fetch_description_html_fast(self, url):

        headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

        try: 
            response = requests.get(url, headers = headers,  timeout = 5)
            response.raise_for_status()

            return response.text
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429:
                return 'BLOCKED_429'
            else:
                print(f'Error HTTP : {http_err}')
                return None
        except Exception as error:
            print(f'There is an Error : {error}')
            return None

    def parse_job_cards(self, html_content, db_object, tech_keywords):

        saved_count = 0

        if html_content == None: return 0
        
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = soup.find_all('h2', class_='job-card-content-middle__title')
    
        for heading in headings:

            it_roles = {'programator', 'developer', 'engineer', 'devops', 'cyber', 'qa', 'tester', 'frontend', 'backend',
                        'fullstack', 'administrator', 'security', 'support', 'sysadmin', 'data', 'cloud'}

            link_tag = heading.find('a')
            if link_tag:
                job = self.create_job_blueprint()
                title_text = link_tag.get_text(strip = True)
                found_role = any(role in title_text.lower() for role in it_roles) 
                found_tech_in_title = any(tech in title_text.lower() for tech in tech_keywords)

                if not found_role and found_tech_in_title:
                    continue

                job_url = link_tag.get('href')  

                if job_url and not job_url.startswith('http'):
                    job_url = 'https://www.ejobs.ro' + job_url

                card_parent = heading.parent
                company_tag = card_parent.find('h3', class_ = 'job-card-content-middle__info--darker')
                company_text = company_tag.get_text(strip = True) if company_tag else 'Unknown'

                location_tag = card_parent.find('div', class_= 'job-card-content-middle__info')
                location_text = location_tag.get_text(strip = True) if location_tag else 'Unknown'

                experience_tag = card_parent.find('div', class_ = 'job-card-content-middle__info')
                info_tags = card_parent.find('div', class_ = 'job-card-content-middle__info')

                experience_text = 'Unknown'
                for tag in info_tags:
                    text_content = tag.get_text(strip = True).lower()
                    if 'level' in text_content or 'ani' in text_content or 'exp' in text_content:
                        experience_text = tag.get_text(strip = True)
                        break

                job['title'] = title_text
                job['link'] = job_url
                job['company'] = company_text
                job['location'] = location_text

                parser = JobParser()

                job['technologies'], job['experience'] = parser.extract_data_from_description(job_url, tech_keywords, self.fetch_description_html_fast)

                time.sleep(1.5)

                job['id'] = self.generate_job_id(title_text, company_text)

                if job['technologies']:
                    db_object.save_jobs_to_db([job])
                    saved_count += 1

        return saved_count

    def generate_job_id(self, title, company):
        
        combined_text = title + company
        hash_object = hashlib.sha256(combined_text.encode('utf-8'))

        return hash_object.hexdigest()
