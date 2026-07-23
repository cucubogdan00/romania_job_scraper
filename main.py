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

async def db_writer_worker(db, queue):

    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break

        job_list, source_name = item
        try:
            if job_list:
                db.save_jobs_to_db(job_list, source_name = source_name)
        except Exception as e:
            logging.error(f"[DB Worker Error] Failed saving batch for {source_name}: {e}")
        finally:
            queue.task_done()

async def run_ejobs(db_queue, tech_keywords):
    ejobs_scraper = EJobsScraper()
    ejobs_categories = [
        'it-software',
        'internet-e-commerce',
        'it-hardware',
        'telecomunicatii',
        'inginerie',
        'productie'
    ]

    total_saved = 0

    for category in ejobs_categories:
        logging.info(f"\n🚀 Switching to category: {category.upper()} 🚀")
        base_url = f'https://www.ejobs.ro/locuri-de-munca/{category}'

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

                loop = asyncio.get_running_loop()
                html_data, _ = await loop.run_in_executor(
                    None, ejobs_scraper.fetch_html_content, url, ejobs_driver
                )

                if not html_data:
                    logging.error(f"Could not fetch HTML for {category} page {page_number}. Skipping category")
                    break

                page_jobs, has_cards = ejobs_scraper.parse_job_cards(html_data, None, tech_keywords)
                if not has_cards:
                    logging.info(f"No jobs found on page {page_number}. Reached end of category {category}.")
                    break
                
                raw_category_jobs.extend(page_jobs)
                page_number += 1
                await asyncio.sleep(2)

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
            
        if raw_category_jobs:
            logging.info(f" Starting async processing for {len(raw_category_jobs)} raw eJobs...")
            processed_jobs = await ejobs_scraper.process_descriptions_await(raw_category_jobs, tech_keywords,batch_size= 5, concurrency= 1 , max_retries= 1,cookies= session_cookies, user_agent=session_user_agent)
            lost_count = len(raw_category_jobs) - len(processed_jobs)
            logging.info(f"[eJobs Category Summary] '{category}': raw={len(raw_category_jobs)} "
                        f"saved={len(processed_jobs)} lost={lost_count}")
            if processed_jobs:
                await db_queue.put((processed_jobs, 'eJobs'))
                total_saved += len(processed_jobs)
                logging.info(f"   [eJobs Filter] Queued '{category}' for DB save ({len(processed_jobs)} jobs).")
        
        logging.info("[Cooldown] Pausing 8s before next eJobs category...")
        await asyncio.sleep(5) 

    return total_saved

async def run_bestjobs(db_queue, tech_keywords):

    bestjobs_scraper = BestJobsScraper()
    bestjobs_categories = [
        'it',
        'telecom',
        'engineering',
        'production',
    ]

    total_saved = 0
    active_driver = None

    for category in bestjobs_categories:
        logging.info(f"\n🚀 Switching to BestJobs category: {category.upper()} 🚀")
        current_url = f"https://www.bestjobs.eu/locuri-de-munca/{category}"

        loop = asyncio.get_running_loop()
        bestjobs_html , live_driver = await loop.run_in_executor(
            None, bestjobs_scraper.fetch_html_content,current_url
        )
        if live_driver:
            active_driver = live_driver

        if bestjobs_html and live_driver:
            raw_bj_jobs = bestjobs_scraper.parse_job_cards(bestjobs_html, None, tech_keywords, live_driver)

            if raw_bj_jobs and isinstance(raw_bj_jobs, list):
                logging.info(f"🔥 Starting async processing for {len(raw_bj_jobs)} raw BestJobs...")
                processed_bj_jobs = await bestjobs_scraper.process_descriptions_await(raw_bj_jobs, tech_keywords)

                if processed_bj_jobs:
                    await db_queue.put((processed_bj_jobs, 'BestJobs'))
                    total_saved += len(processed_bj_jobs)
                    logging.info(f"   [BestJobs Filter] Queued '{category}' for DB save ({len(processed_bj_jobs)} jobs).")
        else:
            logging.error(f"[BestJobs Error] Could not initialize Selenium for BestJobs category {category}.")

    if active_driver:
        logging.info("\n[BestJobs] Closing browser session...")
        active_driver.quit()
    return total_saved


async def main():

    run_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    tech_keywords = {
    # Programming Languages
    'python', 'java', 'c++', 'c#', 'c-sharp', 'php', 'ruby', 'go', 'golang', 
    'rust', 'typescript', 'javascript', 'kotlin', 'scala', 'lua', 'solidity',
    
    # Web & Mobile Frameworks
    'react', 'next.js', 'angular', 'vue', 'nuxt.js', ' Svelte', 'node', 'express', 
    'django', 'flask', 'fastapi', 'spring', 'hibernate', 'asp.net', '.net', 'dotnet', 
    'graphql', 'tailwind', 'wordpress', 'flutter', 'react native', 'ionic',
    
    # Databases & Streaming
    'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'mongo', 
    'oracle', 'sqlserver', 'redis', 'elasticsearch', 'kafka', 'dynamodb', 'cassandra',
    
    # Cloud, DevOps & Infrastructure
    'aws', 'azure', 'gcp', 'cloud', 'docker', 'podman', 'kubernetes', 
    'openshift', 'terraform', 'ansible', 'helm', 'ci/cd', 'bash', 'serverless', 'lambda',
    
    # Cybersecurity & AppSec
    'oauth', 'jwt', 'penetration testing', 'owasp', 'cybersecurity', 'encryption',
    
    # AI, ML & Data Engineering
    'pytorch', 'tensorflow', 'pandas', 'numpy', 'spark', 'hadoop', 'databricks', 'airflow', 'langchain', 'openai',
    
    # Testing, Version Control & API
    'git', 'github', 'gitlab', 'bitbucket', 'selenium', 'cypress', 
    'playwright', 'jmeter', 'postman', 'prometheus', 'grafana', 'wireshark' 
    }

    db = JobDatabase('jobs.db')
    db.init_db()

    db_queue = asyncio.Queue()
    
    writer_task = asyncio.create_task(db_writer_worker(db, db_queue))

    logging.info('Starting Fully Parallel Multi-Platform Scraping Process...')

    results = await asyncio.gather(
        run_ejobs(db_queue, tech_keywords),
        run_bestjobs(db_queue, tech_keywords)
    )

    total_saved_run = sum(results)

    logging.info("\n[DB Queue] Waiting for all pending database writes to complete...")
    await db_queue.join()

    await db_queue.put(None)
    await writer_task

    logging.info(f'\nTotal IT jobs saved during this run: {total_saved_run}')

    ejobs_scraper_instance = EJobsScraper()
    db.check_expired_jobs(ejobs_scraper_instance.fetch_description_html_fast, run_start_time)

    db.generate_market_report()

if __name__ == "__main__":
    
    asyncio.run(main())