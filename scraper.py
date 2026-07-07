import requests
import hashlib
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

    if html_content == None:
        return []
    
    job_list = []
    soup = BeautifulSoup(html_content, 'html.parser')
    headings = soup.find_all('h2', class_='job-card-content-middle__title')

    for heading in headings[:5]:

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

            matched_tech = []
            lower_title = title_text.lower()
            tech_keywords = {'python', 'sap', 'abap', 'cnc', 'siemens', 'java'}

            for keyword in tech_keywords:
                if keyword in lower_title:
                    matched_tech.append(keyword)

            job['technologies'] = matched_tech

            job['id'] = generate_job_id(title_text, company_text)

            job_list.append(job)

    return job_list

def generate_job_id(title, company):
    
    combined_text = title + company
    hash_object = hashlib.sha256(combined_text.encode('utf-8'))

    return hash_object.hexdigest()

if __name__ == "__main__":

    target_url = "https://www.ejobs.ro/locuri-de-munca/programator"

    print("The page is downloading...")
    html_data = fetch_html_content(target_url)

    print("Data is parsing...")
    extracted_jobs = parse_job_cards(html_data)
    
    print(f'I successfully extracted {len(extracted_jobs)} elements: ')
    print(extracted_jobs)