import time

from parser import JobParser
from base_scraper import BaseScraper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class EJobsScraper(BaseScraper):
        
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
        
    def parse_job_cards(self, html_content, db_object, tech_keywords):

        if html_content == None: return 0
        
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = soup.find_all('h2', class_='job-card-content-middle__title')
    
        page_jobs = []

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

                job['title'] = title_text
                job['link'] = job_url
                job['company'] = company_text
                job['location'] = location_text

                parser = JobParser()

                try:
                    job['technologies'], job['experience'], job['work_mode']= parser.extract_data_from_description(job_url, tech_keywords, self.fetch_description_html_fast)
                except Exception as e:
                    print(f"   [Warning] Error parsing description for job '{title_text}': {e}")
                    job['technologies'] = []
                    job['experience'] = 'Unknown'
                    job['work_mode'] = 'On-site'               

                time.sleep(1.5)

                job['id'] = self.generate_job_id(title_text, company_text)

                if job['technologies']:
                    page_jobs.append(job)

        if page_jobs:
            db_object.save_jobs_to_db(page_jobs)
            return len(page_jobs)

        return 0
