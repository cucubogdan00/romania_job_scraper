import time
from scraper import EJobsScraper
from database import JobDatabase

if __name__ == "__main__":

    tech_keywords = {
            'python', 'sap', 'abap', 'cnc', 'siemens', 'java', 'git', 'sql', 'docker', 'linux',
            'javascript', 'react', 'angular', 'html', 'css', 'php', 'c++', 'c#', 'ruby', 'go', 
            'rust', 'typescript', 'vue', 'node', 'postgres', 'mongo', 'kubernetes', 'aws', 
            'azure', 'jenkins', 'selenium', 'cypress', 'jmeter', 'wireshark', 'automation',
            'hana', 'fiori', 'btp', 'basis', 'playwright', 'postman', 'ci/cd', 'bash', 'terraform',
            'c-sharp', 'embedded', 'microcontroller'
                }

    scraper = EJobsScraper()
    db = JobDatabase('jobs.db')

    db.init_db()

    db.check_expired_jobs(scraper.fetch_description_html_fast)

    base_url = 'https://www.ejobs.ro/locuri-de-munca/software'

    total_saved_run = 0

    print('Starting Multi-Page Scraping Process...')

    for page_number in range(1,2):
        if page_number == 1:
            target_url = base_url
        else:
            target_url = f'{base_url}/pagina{page_number}'
    
        print(f'Downloading Page {page_number}...')
        html_data = scraper.fetch_html_content(target_url)
        saved_jobs_count = scraper.parse_job_cards(html_data, db, tech_keywords)
        total_saved_run += saved_jobs_count

        print(f'Successfully saved {saved_jobs_count} IT jobs from Page {page_number}.') 

        if saved_jobs_count == 0:
            print('No more jobs found!Stopping the scraper.')
            break

        if page_number < 10:
            print('Taking a short break to simulate human behaviour (2 seconds)...')
            time.sleep(2)

    print(f'\nTotal IT jobs saved during this run: {total_saved_run}')

    db.generate_market_report()