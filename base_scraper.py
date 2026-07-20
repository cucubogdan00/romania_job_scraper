import hashlib
import requests
import logging
import aiohttp
import asyncio
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

        headers = {
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language' : 'ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7',
            }

        try: 
            response = requests.get(url, headers = headers,  timeout = 20)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429:
                logging.warning(f'[Rate Limit 429 - sync] Blocked on: {url}')
                return 'BLOCKED_429'
            else:
                logging.error(f'[HTTP Error] Status: {http_err}')
                return None
        except Exception as error:
            logging.error(f'[Request Error] Read timed out or network error: {error}')
            return None
        
    async def fetch_description_html_async(self, session, url, headers = None):
        
        if headers is None:
            headers = {
                'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language' : 'ro-RO,ro;q=0.9,en-US;q=0.8 ,en;q=0.7',
                }

        try:
            async with session.get(url, headers = headers ,timeout = 20) as response:
                if response.status == 429:
                    logging.warning(f'[Rate Limit 429 - async] Blocked on: {url}')
                    return 'BLOCKED_429'
                
                response.raise_for_status()

                return await response.text(encoding = 'utf-8')
        except aiohttp.ClientResponseError as http_error:
            logging.error(f'[HTTP Async Error] Status : {http_error.status} for URL: {url}')
            return None
        except Exception as error:
            logging.error(f'[Request Async Error] Network failure or timeout: {error}')
            return None
        
    async def fetch_description_html_curl(self, session, url, headers = None, cookies = None, impersonate = 'chrome'):
        try:
            response = await session.get(
                url, headers = headers, cookies = cookies,
                impersonate = impersonate, timeout = 20
            )

            if response.status_code == 429:
                logging.warning(f'[Rate Limit 429 - curl_cffi] Blocked on: {url}')
                return 'BLOCKED_429'

            response.raise_for_status()
            return response.text

        except Exception as error:
            logging.error(f'[curl_cffi Error] {error} for URL: {url}')
            return None

     