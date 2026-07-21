import time
import logging
import sys
import asyncio

from datetime import datetime
from bs4 import BeautifulSoup
from scraper import EJobsScraper
from database import JobDatabase
from bestjobs_scraper import BestJobsScraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt = "%Y-%m-%d %H-%M-%S",
    handlers = [
        logging.FileHandler('scraper.log', encoding = 'utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

async def main():

    run_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    tech_keywords = {
            'python', 'sap', 'abap', 'cnc', 'siemens', 'java', 'git', 'sql', 'docker', 'linux',
            'javascript', 'react', 'angular', 'html', 'css', 'php', 'c++', 'c#', 'ruby', 'go', 
            'rust', 'typescript', 'vue', 'node', 'postgres', 'mongo', 'kubernetes', 'aws', 
            'azure', 'jenkins', 'selenium', 'cypress', 'jmeter', 'wireshark', 'automation',
            'hana', 'fiori', 'btp', 'basis', 'playwright', 'postman', 'ci/cd', 'bash', 'terraform',
            'c-sharp', 'embedded', 'microcontroller','kafka', 'elasticsearch', 'ansible',
            'jenkins', 'gitlab', 'github', 'bitbucket', 'jira', 'confluence',
            'mongodb', 'postgresql', 'mysql', 'oracle', 'sqlserver', 'golang',
            'react', 'vue', 'angular', 'node', 'express', 'django', 'flask',
            'spring', 'hibernate', 'asp.net', '.net', 'dotnet', 'kotlin', 'scala',
            'docker', 'podman', 'openshift', 'istio', 'prometheus', 'grafana',
            'linux', 'windows', 'macos', 'unix','azure', 'aws', 'gcp', 'cloud', 'helm',
            }

    ejobs_scraper = EJobsScraper()
    bestjobs_scraper = BestJobsScraper()
    db = JobDatabase('jobs.db')

    db.init_db()

    ejobs_categories = [
        'it-software',
        'internet-e-commerce',
        'it-hardware',
        'telecomunicatii',
        'inginerie',
        'productie'
    ]

    bestjobs_categories = [
        'it',
        'telecom',
        'engineering',
        'production',
    ]

    total_saved_run = 0

    logging.info('Starting Multi-Category Scraping Process...')

    for category in ejobs_categories:
        logging.info(f"\n🚀 Switching to category: {category.upper()} 🚀")
        base_url = f'https://www.ejobs.ro/locuri-de-munca/{category}'

        page_number = 1
        raw_category_jobs = []
        session_cookies = None
        session_user_agent = None

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        ejobs_driver = webdriver.Chrome(options=chrome_options)

        try:
            page_number = 1
            while True:
                url = f'{base_url}/pagina{page_number}/'
                logging.info(f"   [eJobs] Loading page {page_number} for {category}...")

                html_data, _ = ejobs_scraper.fetch_html_content(url, driver = ejobs_driver)

                if not html_data:
                    logging.error(f"Could not fetch HTML for {category} page {page_number}. Skipping category")
                    break

                page_jobs = ejobs_scraper.parse_job_cards(html_data, db, tech_keywords)
                if not page_jobs:
                    logging.info(f"No jobs found on page {page_number}. Reached end of category {category}.")
                    break
                  
                raw_category_jobs.extend(page_jobs)
                page_number += 1
                time.sleep(2)

        finally:
            if ejobs_driver:
                try:
                    session_cookies = ejobs_driver.get_cookies()
                    session_user_agent = ejobs_driver.execute_script("return navigator.userAgent;")
                    logging.info(f"   [Session] Captured {len(session_cookies)} cookies + real UA "
                                 f"from the browser session for category '{category}'.")
                except Exception as e:
                    logging.warning(f"   [Session] Could not capture cookies/UA from Selenium: {e}")

                ejobs_driver.quit()

        logging.info(f"   [eJobs] Finished {category}. Total raw jobs collected: {len(raw_category_jobs)}")

            
        if raw_category_jobs:
            logging.info(f" Starting async processing for {len(raw_category_jobs)} raw eJobs...")
            processed_jobs = await ejobs_scraper.process_descriptions_await(raw_category_jobs, tech_keywords,batch_size= 5, concurrency= 1 , max_retries= 1,cookies= session_cookies, user_agent=session_user_agent)
            lost_count = len(raw_category_jobs) - len(processed_jobs)
            logging.info(f"[eJobs Category Summary] '{category}': raw={len(raw_category_jobs)} "
                         f"saved={len(processed_jobs)} lost={lost_count}")
            if processed_jobs:
                db.save_jobs_to_db(processed_jobs, source_name= 'eJobs')
                total_saved_run += len(processed_jobs)
                logging.info(f"   [eJobs Filter] Completed '{category}'. Saved {len(processed_jobs)} relevant jobs!")

        logging.info("[Cooldown] Pausing 8s before next eJobs category...")
        await asyncio.sleep(8) 
        
    active_driver = None

    for category in bestjobs_categories:
        logging.info(f"\n🚀 Switching to BestJobs category: {category.upper()} 🚀")
        current_url = f"https://www.bestjobs.eu/locuri-de-munca/{category}"
        logging.info(f"Downloading {category} from BestJobs...")

        bestjobs_html , live_driver = bestjobs_scraper.fetch_html_content(current_url)

        if live_driver:
            active_driver = live_driver

        if bestjobs_html and live_driver:
            raw_bj_jobs = bestjobs_scraper.parse_job_cards(bestjobs_html, db, tech_keywords, live_driver)

            if raw_bj_jobs and isinstance(raw_bj_jobs, list):
                logging.info(f"🔥 Starting async processing for {len(raw_bj_jobs)} raw BestJobs...")
                processed_bj_jobs = await bestjobs_scraper.process_descriptions_await(raw_bj_jobs, tech_keywords)

                if processed_bj_jobs:
                    db.save_jobs_to_db(processed_bj_jobs, source_name = 'BestJobs')
                    total_saved_run += len(processed_bj_jobs)
                    logging.info(f"   [BestJobs Filter] Completed '{category}'. Saved {len(processed_bj_jobs)} relevant jobs!")
        else:
            logging.error(f"[BestJobs Error] Could not initialize Selenium for BestJobs category {category}.")

    if active_driver:
        logging.info("\n[BestJobs] Closing browser session...")
        active_driver.quit()

    logging.info(f'\nTotal IT jobs saved during this run: {total_saved_run}')
    
    db.check_expired_jobs(ejobs_scraper.fetch_description_html_fast, run_start_time)

    db.generate_market_report()

if __name__ == "__main__":
    
    asyncio.run(main())