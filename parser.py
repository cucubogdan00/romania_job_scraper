import re

from bs4 import BeautifulSoup
class JobParser:

    def parse_location(self, location_text):

        if not location_text:
            return 'N/A', 'On-site'
        
        loc_lower = location_text.lower()

        if 'remote' in loc_lower:
            work_mode = 'Remote'
        elif 'hybrid' in loc_lower or 'hibrid' in loc_lower:
            work_mode = 'Hybrid'
        else:
            work_mode = 'On-site'

        city_clean = location_text
        words_to_remove = ['remote', 'Remote', 'hybrid', 'Hybrid', 'hibrid', 'Hibrid', '(', ')', ',']

        for word in words_to_remove:
            city_clean = city_clean.replace(word, '')

        city_clean = city_clean.strip().strip(',').strip()

        if not city_clean or 'acas' in city_clean.lower():
            city_clean = 'All' if work_mode == 'Remote' else 'N/A'

        return city_clean, work_mode


    def extract_data_from_description(self, job_url, tech_keywords, fetch_func):

        job_html = fetch_func(job_url)

        if job_html == None: return [], 'Unknown', 'Unknown'

        soup = BeautifulSoup(job_html, 'html.parser')
        description_container = soup.find('div' , class_ = 'jobs-show-main-description__section')
        experience_tags = soup.find_all('a' , class_ = 'jobs-show-main-summaries__summary-link')

        if description_container:
            full_text = description_container.get_text(strip = True).lower()
        else:
            body_container = soup.find('body')
            full_text = body_container.get_text(strip = True).lower() if body_container else ""

        experience_text = 'Unknown'
        work_mode_text = 'On-site'

        for tag in experience_tags:
            text_clean = tag.get_text(strip = True).strip(', ')
            text_lower = text_clean.lower()

            if 'level' in text_lower or 'ani' in text_lower or 'exp' in text_lower:
                experience_text = text_clean
                continue

            if 'remote' in text_lower:
                work_mode_text = 'Remote'
            elif 'hibrid' in text_lower or 'hybrid' in text_lower:
                work_mode_text = 'Hybrid'

        found_tech = []
            
        for keyword in tech_keywords:
            
            kw_clean = keyword.lower()
            kw_escaped = re.escape(kw_clean)
            pattern = rf'\b{kw_escaped}\b'

            if re.search(pattern, full_text):
                found_tech.append(keyword)
            
        return found_tech , experience_text, work_mode_text