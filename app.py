import traceback
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
    page_title="Job Matcher AI",
    page_icon="🔥",
    layout="wide",
)

# ... your full custom CSS block here ...
# (Omitted for brevity, but include all your <style> ... </style> markdown block)

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
    st.title("Resume Job Matcher")
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
                api_key_message.markdown('<p style="color: #721c24; background-color: #f8d7da; padding: 8px; border-radius: 4px; font-size: 14px; border: 1px solid #f5c6cb;">❌ Invalid API key. Please check and try again.</p>', unsafe_allow_html=True)
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

    # Main content
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
                            <div class="card">
                                <h3 style="margin-top: 0;">{job.title}</h3>
                                <p><strong>URL:</strong> <a href="{job.url}" target="_blank">{job.url}</a></p>
                                <p><strong>Match:</strong> <span class="match-status {
                                    'good-match' if result["is_match"] else 'poor-match'
                                }">{"✅ Good Match" if result["is_match"] else "❌ Not a Match"}</span></p>
                                <p><strong>Reason:</strong> {result["reason"]}</p>
                                <p><strong>Match Score:</strong> <span style="font-weight: 600;">{result["match_score"]}%</span></p>
                                <div class="match-score-bar">
                                    <div class="match-score-fill {
                                        'match-score-low' if int(result["match_score"]) < 50 else 
                                        'match-score-medium' if int(result["match_score"]) < 75 else 
                                        'match-score-high'
                                    }" style="width: {result["match_score"]}%;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.expander("**Details**", expanded=True):
                                st.markdown("#### Key Strengths:")
                                strengths = result["key_strengths"]
                                if any(strength != "N/A" for strength in strengths):
                                    for strength in strengths:
                                        if strength != "N/A":
                                            st.markdown(f"• {strength}")
                                else:
                                    st.markdown("No specific strengths identified")
                                st.markdown("#### Areas for Improvement:")
                                missing_skills = result["missing_skills"]
                                if any(skill != "N/A" for skill in missing_skills):
                                    for skill in missing_skills:
                                        if skill != "N/A":
                                            st.markdown(f"• {skill}")
                                else:
                                    st.markdown("No specific areas identified")
                                st.markdown("#### Suggestions:")
                                suggestions = result.get("improvement_suggestions", ["N/A"])
                                if any(suggestion != "N/A" for suggestion in suggestions):
                                    for suggestion in suggestions:
                                        if suggestion != "N/A":
                                            st.markdown(f"• {suggestion}")
                                else:
                                    st.markdown("No specific suggestions available")
        except Exception as e:
            if "API key" in str(e) or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                st.markdown('<div class="error-message" style="padding: 10px; margin-bottom: 16px;">❌ Invalid API key. Please check your Firecrawl API key in the sidebar and try again.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-message" style="padding: 10px; margin-bottom: 16px;">❌ An error occurred: {repr(e)}</div>', unsafe_allow_html=True)
                st.text(traceback.format_exc())
        if 'jobs' in locals():
            st.success(f"Analysis complete! Processed {len(jobs)} jobs.")
        else:
            st.success("Analysis complete!")

if __name__ == "__main__":
    asyncio.run(main())