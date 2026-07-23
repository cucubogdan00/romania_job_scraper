# Romania IT Job Scraper

A high-performance, hybrid web scraper designed to collect, parse, and analyze IT and technical job openings from Romania's leading recruitment platforms (eJobs and BestJobs).

The application utilizes Object-Oriented Programming (OOP) principles, is fully containerized with Docker, and uses SQLite for local data persistence.

---

## Features

* **Hybrid Scraping Engine:** Combines Selenium (Chromium Headless) for dynamic page scrolling and lazy-loaded listings with BeautifulSoup4/Requests for fast, asynchronous detail fetching.
* **Modular Architecture:** Cleanly decoupled system divided into distinct classes (`BaseScraper`, `EJobsScraper`, `BestJobsScraper`, `JobParser`, and `JobDatabase`).
* **Intelligent Data Parsing:** Extracts technical keywords, experience levels, and work modes directly from job descriptions using Regular Expressions.
* **Robust Data Merging (UPSERT):** Uses SHA-256 job hashing to generate unique IDs and automatically updates existing entries (reposted jobs) in SQLite.
* **Automated Expiry Checker:** Periodically validates active database entries against the source websites to mark expired roles.
* **Terminal Analytics Reports:** Generates structured statistical summaries showcasing top demanded technologies, work mode splits, and experience level distributions.

---

## Tech Stack

* **Language:** Python 3.9.6+
* **Libraries:** BeautifulSoup4, Requests, Selenium
* **Browser Automation:** Chromium & Chromedriver
* **Database:** SQLite3
* **Containerization:** Docker

---

## Installation & Usage

### Method 1: Running with Docker (Recommended)

The application is pre-configured to run isolated inside a container. To build the image and run the scraper while persisting both the SQLite database and the execution logs on your host machine, execute:

```bash
# 1. Build the Docker image
docker build -t romania_it_job_scraper .

# 2. Run the container with database and log volume mapping
docker run --rm \
  -v $(pwd)/jobs.db:/app/jobs.db \
  -v $(pwd)/scraper.log:/app/scraper.log \
  romania_job_scraper
```

### Method 2: Local Development Environment

If you prefer to run the scraper directly on your local system (make sure you have Google Chrome or Chromium installed):

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python3 main.py
```

---

## Author
Bogdan Cucu - https://github.com/cucubogdan00