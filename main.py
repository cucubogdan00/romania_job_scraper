import time
from scraper import EJobsScraper
from database import JobDatabase

if __name__ == "__main__":

    scraper = EJobsScraper()
    db = JobDatabase('jobs.db')

    db.init_db()

    db.check_expired_jobs(scraper.fetch_description_html_fast)

    all_jobs = []
    base_url = 'https://www.ejobs.ro/locuri-de-munca/software'

    print('Starting Multi-Page Scraping Process...')

    for page_number in range(1,2):
        if page_number == 1:
            target_url = base_url
        else:
            target_url = f'{base_url}/pagina{page_number}'
    
        print(f'Downloading Page {page_number}...')
        html_data = scraper.fetch_html_content(target_url)
        page_jobs = scraper.parse_job_cards(html_data)

        print(f'Successfully extracted {len(page_jobs)} jobs from Page {page_number}.') 

        if len(page_jobs) == 0:
            print('No more jobs found!Stopping the scraper.')
            break

        all_jobs.extend(page_jobs)

        if page_number < 10:
            print('Taking a short break to simulate human behaviour (2 seconds)...')
            time.sleep(2)

    print(f'\nTotal jobs collected : {len(all_jobs)}')

    it_roles = {'programator', 'developer', 'engineer', 'devops', 'cyber', 'qa', 'tester', 'frontend', 'backend', 'fullstack', 'administrator', 'security', 'support'}
    filtered_jobs = []

    for job in all_jobs:
        lower_title = job['title'].lower()

        is_it_job = any(role in lower_title for role in it_roles)

        if is_it_job:
            filtered_jobs.append(job)

    print(f'Jobs matching your tech keywords: {len(filtered_jobs)}')

    db.save_jobs_to_db(filtered_jobs) 

    db.generate_market_report()