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

    categories = [
        'it-software',
        'internet-e-commerce',
        'it-hardware',
        'telecomunicatii',
        'inginerie',
        'productie'
    ]

    total_saved_run = 0

    print('Starting Multi-Category Scraping Process...')

    for category in categories:
        print(f"\n🚀 Switching to category: {category.upper()} 🚀")
        base_url = f'https://www.ejobs.ro/locuri-de-munca/{category}'

        page_number = 1
        all_saved_count = 0

        while page_number <= 30:
            print(f"Downloading {category} - Page {page_number}...")
            current_url = f'{base_url}/pagina{page_number}/'

            html_data = scraper.fetch_html_content(current_url)

            if not html_data:
                print(f"[Error] Could not fetch HTML for {category} page {page_number}. Skipping category")
                break

            saved_jobs_count = scraper.parse_job_cards(html_data, db, tech_keywords)
            total_saved_run += saved_jobs_count

            print(f'Successfully saved {saved_jobs_count} IT jobs from {category} - Page {page_number}.') 

            try:
                soup = BeautifulSoup(html_data, 'html.parser')
                
                next_page_exists = soup.find(lambda tag : tag.name and 'Pagina următoare' in tag.get_text())

                if next_page_exists:
                    print("-> Text 'Pagina următoare' detected. Preparing to advance...")
                    page_number += 1
                    time.sleep(2)
                else:
                    print(f"\n[Pagination] Reached the final page for category {category}")
                    break 
            
            except Exception as e:
                print(f"[Pagination Warning] Error checking next page: {e}. Skipping category.")
                break

    print(f'\nTotal IT jobs saved during this run: {total_saved_run}')

    db.generate_market_report()