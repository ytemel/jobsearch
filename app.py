import streamlit as st
import asyncio
from dotenv import load_dotenv
import os
from src.scraper import JobScraper
from src.matcher import JobMatcher
from src.pdf_processor import PDFProcessor
from firecrawl import FirecrawlApp

# Load environment variables
load_dotenv()

# Set page configuration and theme
st.set_page_config(
    page_title="jobsearch AI",
    page_icon="🔥",
    layout="wide",
)

# --- Custom CSS for jobsearch design system ---
st.markdown("""
<style>
body {
    background: #F3F5F7 !important;
}
.stApp {
    background: #F3F5F7;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    color: #222 !important;
}
h1, h2, h3, h4 {
    color: #181A1B !important;
    font-weight: 700 !important;
}
.sidebar .sidebar-content {
    background: #fff;
}
.stButton > button {
    background: #224DFF !important;
    color: #fff !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 4px rgba(30, 34, 40, 0.05);
}
.stButton > button:disabled {
    background: #B0B5BB !important;
    color: #fff !important;
}
.stTextInput > div > div > input, .stTextArea textarea {
    background: #fff !important;
    border-radius: 8px !important;
    border: 1px solid #DCE0E5 !important;
    color: #222 !important;
    font-size: 16px !important;
}
.stTextInput > label, .stTextArea > label {
    color: #224DFF !important;
    font-weight: 600;
}
.card {
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 1px 8px rgba(50,60,80,0.07);
    padding: 1.6rem 2rem;
    margin-bottom: 2rem;
    border: none;
}
.card h3 {
    color: #224DFF !important;
    margin-bottom: 0.7rem;
}
.card .match-status {
    font-weight: 700;
}
.card .good-match {
    color: #28a745 !important;
}
.card .poor-match {
    color: #dc3545 !important;
}
.card .job-url {
    font-size: 0.93rem;
    word-break: break-all;
}
.match-score-bar {
    height: 8px;
    background: #EDF1FF;
    border-radius: 4px;
    margin-top: 6px;
    margin-bottom: 18px;
    overflow: hidden;
}
.match-score-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}
.match-score-low { background: #dc3545; }
.match-score-medium { background: #f5a623; }
.match-score-high { background: #28a745; }
.st-expander {
    background: #F3F5F7 !important;
    border-radius: 10px !important;
    margin-top: 10px !important;
}
.success-message {
    color: #28a745; 
    background: #eafbe7; 
    padding: 8px; 
    border-radius: 5px; 
    font-size: 15px;
    margin-bottom: 10px;
}
.error-message {
    color: #c82333;
    background: #f8d7da;
    padding: 10px;
    border-radius: 5px;
    font-size: 15px;
    margin-bottom: 10px;
}
.info-box {
    background: #EDF1FF;
    border-radius: 10px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.7rem;
    border-left: 5px solid #224DFF;
}
.source-item {
    background: #EAF0FB;
    border-radius: 6px;
    padding: 0.3rem 0.9rem;
    margin-bottom: 0.4rem;
    border-left: 3px solid #224DFF;
    color: #222;
    font-size: 1rem;
}
</style>
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
    st.title("jobsearch: AI Job Matcher")
    jobs = []

    # Sidebar
    with st.sidebar:
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
            st.markdown('<p style="font-style: italic; font-size: 0.95rem;">No job URLs added yet. Add a job URL above.</p>', unsafe_allow_html=True)
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

    # Main content
    st.markdown("""
    <div class="info-box">
        <h3 style="margin-top: 0;">How It Works</h3>
        <ul>
            <li>Analyze your resume (PDF or pasted text)</li>
            <li>Scrape jobs from your selected job URLs</li>
            <li>AI scores your fit for each job with feedback</li>
        </ul>
        <p style="margin-top: 1.1em;">Upload or paste your resume on the left to begin.</p>
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
                            <div class="card">
                                <h3>{job.title}</h3>
                                <div class="job-url"><strong>URL:</strong> <a href="{job.url}" target="_blank">{job.url}</a></div>
                                <p><strong>Match:</strong> <span class="match-status {'good-match' if result["is_match"] else 'poor-match'}">
                                    {"✅ Good Match" if result["is_match"] else "❌ Not a Match"}</span></p>
                                <p><strong>Reason:</strong> {result["reason"]}</p>
                                <p><strong>Match Score:</strong> <span style="font-weight: 600;">{result["match_score"]}%</span></p>
                                <div class="match-score-bar">
                                    <div class="match-score-fill {'match-score-low' if int(result["match_score"]) < 50 else 'match-score-medium' if int(result["match_score"]) < 75 else 'match-score-high'}"
                                        style="width: {result["match_score"]}%;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.expander("Details", expanded=False):
                                st.markdown("**Key Strengths:**")
                                strengths = result["key_strengths"]
                                if any(strength != "N/A" for strength in strengths):
                                    for strength in strengths:
                                        if strength != "N/A":
                                            st.markdown(f"- {strength}")
                                else:
                                    st.markdown("_No specific strengths identified_")
                                st.markdown("**Areas for Improvement:**")
                                missing_skills = result["missing_skills"]
                                if any(skill != "N/A" for skill in missing_skills):
                                    for skill in missing_skills:
                                        if skill != "N/A":
                                            st.markdown(f"- {skill}")
                                else:
                                    st.markdown("_No specific areas identified_")
                                st.markdown("**Suggestions:**")
                                suggestions = result.get("improvement_suggestions", ["N/A"])
                                if any(suggestion != "N/A" for suggestion in suggestions):
                                    for suggestion in suggestions:
                                        if suggestion != "N/A":
                                            st.markdown(f"- {suggestion}")
                                else:
                                    st.markdown("_No specific suggestions available_")
        except Exception as e:
            if "API key" in str(e) or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                st.markdown('<div class="error-message">❌ Invalid API key. Please check your Firecrawl API key in the sidebar and try again.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-message">❌ An error occurred: {str(e)}</div>', unsafe_allow_html=True)
        if 'jobs' in locals():
            st.success(f"Analysis complete! Processed {len(jobs)} jobs.")
        else:
            st.success("Analysis complete!")

if __name__ == "__main__":
    asyncio.run(main())