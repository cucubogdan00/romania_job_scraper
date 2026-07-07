import requests
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
    
    print(type(job_structure))
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
    items = soup.find_all('li')

    for item in items[:5]:
        jobs = create_job_blueprint()
        text_data = item.get_text(strip = True)
        jobs['title'] = text_data
        job_list.append(jobs)

    return job_list

if __name__ == "__main__":
    job_blueprint = create_job_blueprint()
    print(job_blueprint)

    html_data = fetch_html_content("https://en.wikipedia.org/wiki/Main_Page")
    # print(html_data)

    extracted_jobs = parse_job_cards(html_data)
    print(extracted_jobs)