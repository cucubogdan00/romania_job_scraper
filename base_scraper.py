import hashlib
import requests

class BaseScraper:

    def create_job_blueprint(self):
    
        job_structure = {
            'id': None,              # Will hold the SHA-256 unique hash
            'title': "",             # Will hold the job title string
            'company': "",           # Will hold the company name string
            'location': "",          # Will hold the city / remote status
            'experience' : "",       # Will hold the experience level (Entry-level, Mid-level, Senior-level)
            'work_mode' : "",        # Will hold the work_mode (Remote, Hybrid, On-site)
            'link': "",              # Will hold the URL to the job application
            'technologies': []       # Will hold a list of required skills/tech
        }
        
        return job_structure


    def generate_job_id(self, title, company):
        
        combined_text = title + company
        hash_object = hashlib.sha256(combined_text.encode('utf-8'))
        return hash_object.hexdigest()

        
    def fetch_description_html_fast(self, url):

        headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

        try: 
            response = requests.get(url, headers = headers,  timeout = 20)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429:
                return 'BLOCKED_429'
            else:
                print(f'[HTTP Error] Status: {http_err}')
                return None
        except Exception as error:
            print(f'[Request Error] Read timed out or network error: {error}')
            return None
    