import time 
import hashlib
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from parser import JobParser
from database import JobDatabase

class BestJobsScraper:

    def create_job_blueprint(self):
    
        job_structure = {
            'id': None,              # Will hold the SHA-256 unique hash
            'title': "",             # Will hold the job title string
            'company': "",           # Will hold the company name string
            'location': "",          # Will hold the city / remote status
            'experience' : "",       # Will hold the experience level (Entry-level, Mid-level, Senior-level)
            'work_mode' : "",        # Will hold the work_mode (Remote, Hybrid, On-site)
            'link': "",              # Will hold the URL to the job application
            'technologies': []       # Will hold a list of required skills/tech
        }
        
        return job_structure
    
    
    def fetch_html_content(self, url):

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-gpu')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            time.sleep(4)

            click_count = 0
            max_clicks = 2

            print("   [Selenium] Starting progressive manual scroll and click loop...")

            while click_count < max_clicks:

                last_height = driver.execute_script('return document.body.scrollHeight')

                for i in range(1, 10):
                    target_pixel = int((i / 9) * last_height)
                    driver.execute_script(f'window.scrollTo(0, {target_pixel});')
                    time.sleep(0.5)

                time.sleep(2)
               
                try:
                    button = driver.find_element(By.CSS_SELECTOR, "button.bg-secondary")
                    if button.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(1)
                        button.click()
                        click_count += 1
                        print(f"   [Selenium] Clicked 'Load more' ({click_count}/{max_clicks}). Loading next batch...")                
                        time.sleep(3)
                    else:
                        print("   [Pagination] 'Load more' button is hidden. Reached the end.")
                        break
                    
                except Exception:
                    print("   [Pagination] Reached the end of the category (Button not found anymore).")
                    break
                        
            full_html = driver.page_source
            soup = BeautifulSoup(full_html, 'html.parser')
            job_links = soup.find_all('a', class_ = 'absolute inset-0 z-1')
            print(f"\n[Soup] Total jobs loaded after deep scroll: {len(job_links)} !")

            return full_html, driver

        except Exception as error:
            print(f'Selenium Automation Error during fetch: {error}')        
            return None, None
    
    def fetch_description_html_selenium(self, url, driver):
        try:
            driver.get(url)
            time.sleep(1.2)  # Pauză mică să apuce să încarce textul jobului
            return driver.page_source
        except Exception as error:
            print(f"Eroare la încărcarea descrierii cu Selenium: {error}")
            return None 
        
        
    def fetch_description_html_fast(self, url):

        headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

        try: 
            response = requests.get(url, headers = headers,  timeout = 10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429:
                return 'BLOCKED_429'
            else:
                print(f'[HTTP Error] Status: {http_err}')
                return None
        except Exception as error:
            print(f'[Request Error] Read timed out or network error: {error}')
            return None
        
    def parse_job_cards(self, html_content, db_object, tech_keywords, driver):

        saved_count = 0

        if html_content == None: return 0
        
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = soup.find_all('a', class_='absolute inset-0 z-1')
    
        page_jobs = []

        for link_tag in headings:

            it_roles = {'programator', 'developer', 'engineer', 'devops', 'cyber', 'qa', 'tester', 'frontend', 'backend',
                        'fullstack', 'administrator', 'security', 'support', 'sysadmin', 'data', 'cloud'}

            if link_tag:
                job = self.create_job_blueprint()

                job_url = link_tag.get('href')  

                if job_url and not job_url.startswith('http'):
                    job_url = 'https://www.bestjobs.eu' + job_url

                card_parent = link_tag.find_parent('div')
                if not card_parent:
                    continue

                title_tag = card_parent.find('h2', class_ = 'line-clamp-2')
                title_text = title_tag.get_text(strip = True) if title_tag else 'Unknown'
                found_role = any(role in title_text.lower() for role in it_roles) 
                found_tech_in_title = any(tech in title_text.lower() for tech in tech_keywords)

                if not found_role and found_tech_in_title:
                    continue

                company_tag = card_parent.find('div', class_ = 'text-ink-medium')
                company_text = company_tag.get_text(strip = True) if company_tag else 'Unknown'

                location_tag = card_parent.find('div', class_= 'relative z-2')
                location_text = location_tag.get_text(strip = True) if location_tag else 'Unknown'

                job['title'] = title_text
                job['link'] = job_url
                job['company'] = company_text
                job['location'] = 'Unknown'

                parser = JobParser()

                try:
                    fetch_func = self.fetch_description_html_fast
                    job['technologies'], job['experience'], job['work_mode'], real_location = parser.extract_data_from_bestjobs_description(job_url, tech_keywords, fetch_func)
                
                    if real_location and real_location != 'Unknown':
                        job['location'] = real_location

                except Exception as e:
                    print(f"   [Warning] Error parsing description: {e}")
                    job['technologies'] = []
                    job['experience'] = 'Unknown'
                    job['work_mode'] = 'On-site' 
                    job['location'] = 'Unknown'   

                if job['location'] == 'Unknown' and location_text and location_text != 'Unknown':
                    exp_keywords = ['junior', 'middle', 'senior', 'entry', 'executive', 'ani', 'experien']
                    if not any(exp_kw in location_text.lower() for exp_kw in exp_keywords) and not any(char.isdigit() for char in location_text):
                        job['location'] = location_text
                
                if job['work_mode'] in ['On-site', 'Unknown'] and location_text:
                    loc_lower = location_text.lower()
                    if 'remote' in loc_lower:
                        job['work_mode'] = 'Remote'
                        job['location'] = 'Remote'
                    elif 'hibrid' in loc_lower or 'hybrid' in loc_lower:
                        job['work_mode'] = 'Hybrid'

                if job['experience'] == 'Unknown' and location_text:
                    loc_lower = location_text.lower()
                    if 'entry' in loc_lower or '0-2' in loc_lower or 'fără' in loc_lower:
                        job['experience'] = 'Entry-Level (< 2 ani)'
                    elif 'mid' in loc_lower or '2-5' in loc_lower or 'middle' in loc_lower:
                        job['experience'] = 'Mid-Level (2-5 ani)'
                    elif 'senior' in loc_lower or '5-10' in loc_lower:
                        job['experience'] = 'Senior-Level (> 5 ani)'
          

                time.sleep(1.5)

                job['id'] = self.generate_job_id(title_text, company_text)

                if job['technologies']:
                    page_jobs.append(job)

        if page_jobs:
            db_object.save_jobs_to_db(page_jobs, source_name = 'BestJobs')
            return len(page_jobs)

        return 0
    

    def generate_job_id(self, title, company):
        
        combined_text = title + company
        hash_object = hashlib.sha256(combined_text.encode('utf-8'))
        return hash_object.hexdigest()

if __name__ == "__main__":
    real_test_db = JobDatabase("test_bestjobs.db") 
    real_test_db.init_db()

    scraper = BestJobsScraper()

    tech_keywords = {
            'python', 'sap', 'abap', 'cnc', 'siemens', 'java', 'git', 'sql', 'docker', 'linux',
            'javascript', 'react', 'angular', 'html', 'css', 'php', 'c++', 'c#', 'ruby', 'go', 
            'rust', 'typescript', 'vue', 'node', 'postgres', 'mongo', 'kubernetes', 'aws', 
            'azure', 'jenkins', 'selenium', 'cypress', 'jmeter', 'wireshark', 'automation',
            'hana', 'fiori', 'btp', 'basis', 'playwright', 'postman', 'ci/cd', 'bash', 'terraform',
            'c-sharp', 'embedded', 'microcontroller'
            }
    test_url = "https://www.bestjobs.eu/locuri-de-munca/it"

    print("[Test] Initializing BestJobs page download...")
    html, live_driver = scraper.fetch_html_content(test_url)

    if html and live_driver:
        print("[Test] Starting card parsing and saving into test_bestjobs.db...")
        total_saved = scraper.parse_job_cards(html, real_test_db, tech_keywords, live_driver)
        print(f"\n[Test Completed] Successfully saved jobs: {total_saved}")
    else:
        print("[Test Failed] Could not initialize Selenium.")