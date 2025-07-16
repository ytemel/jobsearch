from urllib import response
from firecrawl import FirecrawlApp
from .models import Job, JobListings
import streamlit as st
import os

@st.cache_data(show_spinner=False)
def _cached_parse_resume(pdf_link: str) -> str:
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("Firecrawl API key is required. Please enter it in the sidebar.")
    app = FirecrawlApp(api_key=api_key)
    response = app.scrape_url(url=pdf_link)
    return response["markdown"]

class JobScraper:
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("Firecrawl API key is required. Please enter it in the sidebar.")
        self.app = FirecrawlApp(api_key=api_key)

    async def parse_resume(self, pdf_link: str) -> str:
        return _cached_parse_resume(pdf_link)

    async def scrape_job_postings(self, source_urls: list[str]) -> list[Job]:
        response = self.app.batch_scrape_urls(
            urls=source_urls,
            formats=["extract"],
            extract={
                "schema": JobListings.model_json_schema(),
                "prompt": "Extract information based on the schema provided",
            },
        )

        jobs = []
        for job in response.data:
            # Try dot notation first, fall back to dict if needed
            if hasattr(job.extract, "jobs"):
                jobs.extend(job.extract.jobs)
            else:
                jobs.extend(job.extract["jobs"])

        return [Job(**job) for job in jobs]

    async def scrape_job_content(self, job_url: str) -> str:
        response = self.app.scrape_url(url=job_url)
        return response.markdown