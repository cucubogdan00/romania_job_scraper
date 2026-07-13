import time
from bs4 import BeautifulSoup
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

    page_number = 1
    all_saved_count = 0

    while page_number <= 30:
        print(f"Downloading Page {page_number}...")

        current_url = f'{base_url}/pagina{page_number}/'

        html_data = scraper.fetch_html_content(current_url)

        if not html_data:
            print(f"[Error] Could not fetch HTML content for page {page_number}. Stopping.")
            break

        saved_jobs_count = scraper.parse_job_cards(html_data, db, tech_keywords)
        total_saved_run += saved_jobs_count

        print(f'Successfully saved {saved_jobs_count} IT jobs from Page {page_number}.') 

        try:
            soup = BeautifulSoup(html_data, 'html.parser')
            
            next_page_exists = soup.find(lambda tag : tag.name and 'Pagina următoare' in tag.get_text())

            if next_page_exists:
                print("-> Text 'Pagina următoare' detected. Preparing to advance...")
                page_number += 1
                time.sleep(2)
            else:
                print("\n[Pagination] No 'Pagina următoare' text found. We have reached the final page!")
                break 
        
        except Exception as e:
            print(f"[Pagination Warning] Could not check next page: {e}. Stopping run to be safe.")
            break

    print(f'\nTotal IT jobs saved during this run: {total_saved_run}')

    db.generate_market_report()