import streamlit as st
import asyncio
from dotenv import load_dotenv
import os
from src.scraper import JobScraper
from src.matcher import JobMatcher
from src.pdf_processor import PDFProcessor
from firecrawl import FirecrawlApp

# --- Page Config ---
st.set_page_config(page_title="jobsearch", page_icon="🔍", layout="wide")
load_dotenv()

# --- CSS for Jobsearch Design ---
st.markdown("""
<style>
body {
    background: #f3f2ef;
}

.jobsearch-navbar {
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 0.7rem 0 0.5rem 0;
    background: #fff;
    border-bottom: 1px solid #e6e6e6;
    margin-bottom: 1.5rem;
    position: sticky;
    top: 0;
    z-index: 100;
}
.jobsearch-navbar .nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #666;
    text-decoration: none;
    font-size: 0.92rem;
    font-weight: 500;
    transition: color 0.2s;
}
.jobsearch-navbar .nav-item.selected {
    color: #222;
    font-weight: 700;
}
.jobsearch-navbar .nav-item.selected .nav-underline {
    width: 32px;
    height: 3px;
    background: #222;
    border-radius: 2px;
    margin-top: 4px;
    display: block;
}
.jobsearch-navbar .nav-item:not(.selected):hover {
    color: #222;
}
.jobsearch-search {
    width: 100%;
    max-width: 340px;
    margin: 1.7rem auto 1rem auto;
    display: flex;
    align-items: center;
    background: #fff;
    border: 2px solid #d1d1d1;
    border-radius: 2rem;
    box-shadow: 0 2px 8px rgba(40,40,40,0.02);
    padding: 0.22rem 1.1rem;
    font-size: 1.17rem;
    gap: 0.5rem;
}
.jobsearch-search input {
    border: none;
    outline: none;
    font-size: 1.13rem;
    width: 100%;
    padding: 0.7rem 0;
    background: transparent;
    color: #444;
}
.jobsearch-search .search-icon {
    color: #767676;
    font-size: 1.5rem;
    margin-right: 0.2rem;
}
.jobsearch-sidebar {
    background: #fff;
    border-radius: 1rem;
    padding: 1.3rem 1rem;
    box-shadow: 0 2px 8px rgba(60,60,60,0.07);
}
.jobsearch-card {
    background: #fff;
    border-radius: 1rem;
    box-shadow: 0 2px 12px rgba(40,40,40,0.08);
    padding: 2rem 2.2rem 1.7rem 2.2rem;
    margin-bottom: 2rem;
    border: 1px solid #ececec;
}
.match-score-bar {
    height: 8px;
    background-color: #e9ecef;
    border-radius: 4px;
    margin-top: 5px;
    overflow: hidden;
}
.match-score-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s;
}
.match-score-low {
    background-color: #dc3545;
}
.match-score-medium {
    background-color: #ffc107;
}
.match-score-high {
    background-color: #28a745;
}
.stButton>button {
    border-radius: 2rem !important;
    padding: 0.55rem 2.1rem !important;
    font-weight: 600;
    background: #004182 !important;
    color: #fff !important;
    border: none !important;
    transition: background 0.2s;
}
.stButton>button:hover {
    background: #014a96 !important;
}
.stTextInput>div>input, .stTextArea>div>textarea {
    border-radius: 1.5rem !important;
    border: 1.5px solid #dadada !important;
    padding: 0.7rem 1.2rem !important;
}
.stSidebar [data-testid="stSidebarContent"] {
    padding-top: 1.5rem !important;
}
.stExpander, .st-expander {
    border-radius: 1.1rem !important;
    background: #f9f9f9 !important;
}
.success-message {
    color: #28a745; background-color: #e8f5e9;
    padding: 8px; border-radius: 4px; font-size: 14px;
}
.error-message {
    color: #721c24; background-color: #f8d7da;
    padding: 10px; border-radius: 4px; font-size: 14px; border: 1px solid #f5c6cb;
}
.info-box {
    background: #f2fafc;
    border-left: 3px solid #0066cc;
    border-radius: 10px;
    padding: 1rem 2rem;
    margin-bottom: 1.8rem;
}
</style>
""", unsafe_allow_html=True)

# --- Custom SVG Icons ---
def svg_icon(icon):
    if icon == "home":
        return '<svg xmlns="http://www.w3.org/2000/svg" width="25" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 22"><path d="M3 9.9 12 3l9 6.9"/><path d="M4 10v8.1c0 .5.4.9.9.9h4.6c.5 0 .9-.4.9-.9V14c0-.5.4-.9.9-.9h1.4c.5 0 .9.4.9.9v4.9c0 .5.4.9.9.9h4.6c.5 0 .9-.4.9-.9V10"/></svg>'
    if icon == "network":
        return '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="9" cy="7" r="4"/><circle cx="17" cy="17" r="4"/><path d="M15.59 15.59 12 12m0 0V8m0 4 3.59 3.59"/></svg>'
    if icon == "jobs":
        return '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="13" rx="2"/><path d="M16 7V5a4 4 0 0 0-8 0v2"/></svg>'
    if icon == "chat":
        return '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15.5A2.5 2.5 0 0 1 18.5 18h-13A2.5 2.5 0 0 1 3 15.5V7A2.5 2.5 0 0 1 5.5 4.5h13A2.5 2.5 0 0 1 21 7v8.5Z"/><path d="m8 11 4 4 4-4"/></svg>'
    if icon == "bell":
        return '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
    if icon == "search":
        return '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 22 22"><circle cx="11" cy="11" r="8"/><path d="m19 19-4-4"/></svg>'
    return ""

# --- Jobsearch Navigation Bar ---
st.markdown(f"""
<div class="jobsearch-navbar">
    <div class="nav-item selected">{svg_icon("home")}<span>Home</span><span class="nav-underline"></span></div>
    <div class="nav-item">{svg_icon("network")}<span>My Network</span></div>
    <div class="nav-item">{svg_icon("jobs")}<span>Jobs</span></div>
    <div class="nav-item">{svg_icon("chat")}<span>Messaging</span></div>
    <div class="nav-item">{svg_icon("bell")}<span>Notifications</span></div>
</div>
""", unsafe_allow_html=True)

# --- Jobsearch Search Bar ---
st.markdown(f"""
<div class="jobsearch-search">
    <span class="search-icon">{svg_icon("search")}</span>
    <input placeholder="Search" disabled />
</div>
""", unsafe_allow_html=True)

# ---------- Functions ----------

async def process_job(scraper, matcher, job, resume_content):
    try:
        job_content = await scraper.scrape_job_content(job.url)
        result = await matcher.evaluate_match(resume_content, job_content)
        try:
            int(result["match_score"])
        except (ValueError, TypeError):
            result["match_score"] = '0'
        result["is_match"] = result["is_match"] and int(result["match_score"]) >= 50
    except Exception as e:
        result = {
            "is_match": False,
            "reason": f"Error processing job: {str(e)}",
            "match_score": "0",
            "key_strengths": ["N/A"],
            "missing_skills": ["N/A"],
            "improvement_suggestions": ["N/A"]
        }
    return job, result

async def main():
    st.title("jobsearch")
    jobs = []

    # --- Sidebar (jobsearch style) ---
    with st.sidebar:
        st.markdown('<div class="jobsearch-sidebar">', unsafe_allow_html=True)
        st.markdown("<h3>Configuration</h3>", unsafe_allow_html=True)
        firecrawl_api_key = st.text_input(
            "Firecrawl API Key",
            value=os.getenv("FIRECRAWL_API_KEY", ""),
            type="password",
            placeholder="Enter your Firecrawl API key",
            help="Your Firecrawl API key is required to parse resumes and job listings"
        )
        if firecrawl_api_key:
            firecrawl_api_key = firecrawl_api_key.strip()
            os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key
            api_key_message = st.empty()
            try:
                test_app = FirecrawlApp(api_key=firecrawl_api_key)
                api_key_message.markdown('<p class="success-message">✅ API key successfully set</p>', unsafe_allow_html=True)
            except Exception as e:
                api_key_message.markdown('<p class="error-message">❌ Invalid API key. Please check and try again.</p>', unsafe_allow_html=True)
                os.environ.pop("FIRECRAWL_API_KEY", None)

        st.divider()
        st.markdown("<h3>Manage Job URLs</h3>", unsafe_allow_html=True)
        new_url = st.text_input(
            "Add Job URL",
            placeholder="https://www.company.com/jobs/position",
            key="new_url_input"
        )
        if 'job_urls' not in st.session_state:
            st.session_state.job_urls = []
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("Add URL", key="add_url_btn", help="Add this URL to your job list", use_container_width=True, disabled=(not new_url)):
                if new_url not in st.session_state.job_urls:
                    st.session_state.job_urls.append(new_url)
                    st.success("Job URL added!")
                else:
                    st.warning("This URL is already in your list.")
        st.markdown("<h4>Current Job URLs</h4>", unsafe_allow_html=True)
        if not st.session_state.job_urls:
            st.markdown('<p style="font-style: italic; font-size: 0.9rem;">No job URLs added yet. Add a job URL above.</p>', unsafe_allow_html=True)
        for i, url in enumerate(st.session_state.job_urls):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f'<div class="source-item">{url}</div>', unsafe_allow_html=True)
            with col2:
                if st.button("Delete", key=f"{i}_delete", help="Remove this job URL"):
                    st.session_state.job_urls.remove(url)
                    st.rerun()
        st.divider()
        st.markdown("<h3>Resume Analysis</h3>", unsafe_allow_html=True)
        resume_input_method = st.radio(
            "Resume Input Method",
            ["File Upload", "URL Input", "Text Input"],
            label_visibility="collapsed",
            horizontal=True,
            index=0
        )
        if resume_input_method == "URL Input":
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px;">Enter Resume PDF URL</p>', unsafe_allow_html=True)
            resume_url = st.text_input(
                label="Resume URL",
                placeholder="https://www.website.com/resume.pdf",
                label_visibility="collapsed",
                key="resume_url_input"
            )
            resume_file = None
            resume_text = None
        elif resume_input_method == "File Upload":
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px;">Upload Resume PDF</p>', unsafe_allow_html=True)
            resume_file = st.file_uploader(
                "Upload Resume",
                type=["pdf"],
                label_visibility="collapsed",
                key="resume_file_input"
            )
            resume_url = ""
            resume_text = None
        else:
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px;">Paste Resume Text</p>', unsafe_allow_html=True)
            resume_text = st.text_area(
                label="Resume Text",
                placeholder="Paste the content of your resume here...",
                height=300,
                label_visibility="collapsed",
                key="resume_text_input"
            )
            resume_url = ""
            resume_file = None
        analyze_button = st.button(
            "Analyze Resume",
            use_container_width=True,
            disabled=(not resume_url and resume_file is None and not resume_text)
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Main content area (jobsearch card style) ---
    st.markdown("""
    <div class="info-box">
        <h3 style="margin-top: 0;">How It Works</h3>
        <p>This app helps you find matching jobs by:</p>
        <ul>
            <li>Analyzing your resume from a PDF file or URL</li>
            <li>Scraping job postings from your saved job sources</li>
            <li>Using AI to evaluate if you're a good fit for each position</li>
        </ul>
        <p>Simply upload your resume PDF in the sidebar to get started!</p>
    </div>
    """, unsafe_allow_html=True)

    if not os.getenv("FIRECRAWL_API_KEY"):
        st.markdown("""
            <div style="
                padding: 0.75rem; 
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-radius: 0.25rem;
                color: #1f1f1f;
                font-weight: 500;
                margin-bottom: 1rem;">
                ⚠️ Please enter your Firecrawl API key in the sidebar to continue.
            </div>
        """, unsafe_allow_html=True)
        return

    if analyze_button and (resume_url or resume_file or resume_text):
        try:
            scraper = JobScraper()
            matcher = JobMatcher()
            with st.spinner("Parsing resume..."):
                if resume_url:
                    resume_content = await scraper.parse_resume(resume_url)
                elif resume_file:
                    pdf_processor = PDFProcessor()
                    resume_content = pdf_processor.extract_text_from_pdf(resume_file)
                else:
                    resume_content = resume_text
            job_urls = st.session_state.job_urls
            if not job_urls:
                st.warning("No job URLs provided. Please add some in the sidebar!")
                return
            with st.spinner("Scraping job postings..."):
                jobs = await scraper.scrape_job_postings(job_urls)
            if not jobs:
                st.warning("No jobs found in the provided URLs.")
                return
            with st.spinner(f"Analyzing {len(jobs)} jobs..."):
                tasks = []
                for job in jobs:
                    task = process_job(scraper, matcher, job, resume_content)
                    tasks.append(task)
                results_container = st.container()
                with results_container:
                    st.markdown("<h2>Job Matches</h2>", unsafe_allow_html=True)
                    job_results = []
                    for coro in asyncio.as_completed(tasks):
                        job, result = await coro
                        try:
                            int(result["match_score"])
                        except (ValueError, TypeError):
                            result["match_score"] = '0'
                        job_results.append((job, result))
                    job_results.sort(key=lambda x: int(x[1]["match_score"]), reverse=True)
                    for job, result in job_results:
                        with st.container():
                            st.markdown(f"""
                            <div class="jobsearch-card">
                                <h3 style="margin-top: 0;">{job.title}</h3>
                                <p><strong>URL:</strong>