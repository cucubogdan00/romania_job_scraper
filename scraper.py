import requests
import hashlib
import csv

from bs4 import BeautifulSoup

def create_job_blueprint():
   
    job_structure = {
        'id': None,              # Will hold the SHA-256 unique hash
        'title': "",             # Will hold the job title string
        'company': "",           # Will hold the company name string
        'location': "",          # Will hold the city / remote status
        'link': "",              # Will hold the URL to the job application
        'technologies': []       # Will hold a list of required skills/tech
     }
    
    return job_structure

def fetch_html_content(url):

    custom_headers = {
        'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers = custom_headers, timeout = 10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as error:
        print(f'The Error is : {error}')
        return None

def parse_job_cards(html_content):

    if html_content == None: return []
    
    job_list = []
    soup = BeautifulSoup(html_content, 'html.parser')
    headings = soup.find_all('h2', class_='job-card-content-middle__title')

    for heading in headings:

        link_tag = heading.find('a')
        if link_tag:
            job = create_job_blueprint()
            title_text = link_tag.get_text(strip = True)
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

            tech_keywords = {'python', 'sap', 'abap', 'cnc', 'siemens', 'java', 'git', 'sql', 'docker', 'linux'}
            job['technologies'] = extract_technologies_from_description(job_url, tech_keywords)

            job['id'] = generate_job_id(title_text, company_text)

            job_list.append(job)

    return job_list

def generate_job_id(title, company):
    
    combined_text = title + company
    hash_object = hashlib.sha256(combined_text.encode('utf-8'))

    return hash_object.hexdigest()

def extract_technologies_from_description(job_url, tech_keywords):

    job_html = fetch_html_content(job_url)

    if job_html == None: return []

    soup = BeautifulSoup(job_html, 'html.parser')
    description_container = soup.find('div' , class_ = 'jobs-show-main-description__section')

    if description_container:
        full_text = description_container.get_text(strip = True).lower()
        found_tech = []
        
        for keyword in tech_keywords:
            if keyword in full_text:
                found_tech.append(keyword)
        
        return found_tech

    return []

def save_jobs_to_csv(job_list, filename = 'jobs.csv'):

    if job_list == []:
        print('The list is EMPTY!!!')
        return
    
    headers = ['id', 'title', 'company', 'location', 'link', 'technologies']

    with open(filename, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        for job in job_list:

            row_data = job.copy()
            row_data['technologies'] = ', '.join(job['technologies'])
            writer.writerow(row_data)
    
    print(f'Successfully saved {len(job_list)} jobs to {filename}!')


if __name__ == "__main__":

    all_jobs = []
    base_url = 'https://www.ejobs.ro/locuri-de-munca/software'

    print('Starting Multi-Page Scraping Process...')

    for page_number in range(1,4):
        if page_number == 1:
            target_url = base_url
        else:
            target_url = f'{base_url}/pagina{page_number}'
    
        print(f'Downloading Page {page_number}...')
        html_data = fetch_html_content(target_url)
        page_jobs = parse_job_cards(html_data)

        print(f'I successfully extracted {len(page_jobs)} jobs from Page {page_number}.') 

        if len(page_jobs) == 0:
            print('No more jobs found!Stopping the scraper.')
            break

        all_jobs.extend(page_jobs)

    print(f'\nTotal jobs collected : {len(all_jobs)}')
    save_jobs_to_csv(all_jobs)