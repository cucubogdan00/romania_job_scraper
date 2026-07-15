import time
from bs4 import BeautifulSoup
from scraper import EJobsScraper
from database import JobDatabase
from bestjobs_scraper import BestJobsScraper

if __name__ == "__main__":

    tech_keywords = {
            'python', 'sap', 'abap', 'cnc', 'siemens', 'java', 'git', 'sql', 'docker', 'linux',
            'javascript', 'react', 'angular', 'html', 'css', 'php', 'c++', 'c#', 'ruby', 'go', 
            'rust', 'typescript', 'vue', 'node', 'postgres', 'mongo', 'kubernetes', 'aws', 
            'azure', 'jenkins', 'selenium', 'cypress', 'jmeter', 'wireshark', 'automation',
            'hana', 'fiori', 'btp', 'basis', 'playwright', 'postman', 'ci/cd', 'bash', 'terraform',
            'c-sharp', 'embedded', 'microcontroller'
            }

    ejobs_scraper = EJobsScraper()
    bestjobs_scraper = BestJobsScraper()
    db = JobDatabase('jobs.db')

    db.init_db()

    #db.check_expired_jobs(ejobs_scraper.fetch_description_html_fast)

    ejobs_categories = [
        'it-software',
      #  'internet-e-commerce',
      #  'it-hardware',
      #  'telecomunicatii',
      #  'inginerie',
      #  'productie'
    ]

    bestjobs_categories = [
        'it',
        #'telecom'
        #'engineering',
        #'production',
    ]

    total_saved_run = 0

    print('Starting Multi-Category Scraping Process...')

    for category in ejobs_categories:
        print(f"\n🚀 Switching to category: {category.upper()} 🚀")
        base_url = f'https://www.ejobs.ro/locuri-de-munca/{category}'

        page_number = 1
        all_saved_count = 0

        while page_number <= 1:
            print(f"Downloading {category} - Page {page_number}...")
            current_url = f'{base_url}/pagina{page_number}/'

            html_data = ejobs_scraper.fetch_html_content(current_url)

            if not html_data:
                print(f"[Error] Could not fetch HTML for {category} page {page_number}. Skipping category")
                break

            saved_jobs_count = ejobs_scraper.parse_job_cards(html_data, db, tech_keywords)
            total_saved_run += saved_jobs_count
            all_saved_count += saved_jobs_count

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
        
        print(f"   [eJobs Filter] Completed category '{category}'. Successfully saved {all_saved_count} relevant jobs in total from this category!")

    print(f'\nTotal IT jobs saved during this run: {total_saved_run}')

    active_driver = None

    for category in bestjobs_categories:
        print(f"\n🚀 Switching to BestJobs category: {category.upper()} 🚀")
        current_url = f"https://www.bestjobs.eu/locuri-de-munca/{category}"
        print(f"Downloading {category} from BestJobs...")

        bestjobs_html , live_driver = bestjobs_scraper.fetch_html_content(current_url)

        if live_driver:
            active_driver = live_driver

        if bestjobs_html and live_driver:
            print("[BestJobs] Parsing cards and fetching descriptions...")
            soup_temp = BeautifulSoup(bestjobs_html, 'html.parser')
            total_loaded = len(soup_temp.find_all('a', class_ = 'absolute inset-0 z-1'))
            saved_bestjobs = bestjobs_scraper.parse_job_cards(bestjobs_html, db, tech_keywords, live_driver)
            total_saved_run += saved_bestjobs

            print(f"   [BestJobs Filter] Out of {total_loaded} loaded jobs in category '{category}', successfully saved {saved_bestjobs} relevant jobs in DB!")
            print(f"[BestJobs] Successfully saved {saved_bestjobs} IT jobs from category {category}.")        
        else:
            print(f"[BestJobs Error] Could not initialize Selenium for BestJobs category {category}.")

    if active_driver:
        print("\n[BestJobs] Closing browser session...")
        active_driver.quit()

    db.generate_market_report()