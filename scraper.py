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

if __name__ == "__main__":
    job_blueprint = create_job_blueprint()
    print(job_blueprint)
    