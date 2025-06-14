import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = f"Job Scraper <mailgun@{MAILGUN_DOMAIN}>"

WORKDAY_URL = "https://foundationccc.wd1.myworkdayjobs.com/fccc-careers"


def scrape_jobs():
    # use Playwright to render dynamic content
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(WORKDAY_URL, wait_until="networkidle")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    job_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/fccc-careers/job"):
            full_url = f"https://foundationccc.wd1.myworkdayjobs.com{href}"
            if full_url not in job_links:
                job_links.append(full_url)

    return job_links


def send_email(job_links):
    if not job_links:
        print("✅ No new jobs found.")
        return

    body = "🚨 New jobs found:\n\n" + "\n".join(job_links)

    resp = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": "New Job Postings Found",
            "text": body,
        },
    )

    if resp.status_code == 200:
        print("✅ Email sent successfully via Mailgun.")
    else:
        print(f"❌ Failed to send email. Status: {resp.status_code}")
        print(resp.text)


if __name__ == "__main__":
    jobs = scrape_jobs()
    print("🔍 Jobs scraped:", len(jobs))
    send_email(jobs)
