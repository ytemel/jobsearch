from langchain_openai import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import ChatPromptTemplate
from typing import Dict
import re

class JobMatcher:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

        self.response_schemas = [
            ResponseSchema(
                name="is_match",
                description="Whether the candidate is a good fit for the job (true/false)",
            ),
            ResponseSchema(
                name="reason",
                description="Brief explanation of why the candidate is or isn't a good fit",
            ),
            ResponseSchema(
                name="match_score",
                description="A score from 0-100 representing how well the candidate matches the job requirements",
            ),
            ResponseSchema(
                name="key_strengths",
                description="List of 2-3 key strengths the candidate has for this position",
            ),
            ResponseSchema(
                name="missing_skills",
                description="List of 1-2 important skills or qualifications the candidate is missing (if any)",
            ),
            ResponseSchema(
                name="improvement_suggestions",
                description="List of 1-2 suggestions for how the candidate could improve their qualifications for this role",
            ),
        ]

        self.prompt = ChatPromptTemplate.from_template(
            """
            You are an expert resume reviewer and job matcher. Your task is to evaluate if a candidate is a good fit for a job based on their resume and the job posting.

            First, carefully analyze the resume to identify the candidate's skills, experience, education, and qualifications.
            Then, compare these to the requirements in the job posting.

            Consider both hard skills (technical abilities, certifications, etc.) and soft skills (communication, teamwork, etc.).

            Important: For key_strengths, missing_skills, and improvement_suggestions, provide clean, simple text items without HTML tags or special formatting. Each item should be a complete, concise sentence or phrase.

            Resume:
            {resume}

            Job Posting:
            {job_posting}

            {format_instructions}
            """
        )

        self.output_parser = StructuredOutputParser.from_response_schemas(
            self.response_schemas
        )

    async def evaluate_match(self, resume: str, job_posting: str) -> Dict:
        try:
            if not resume or resume.startswith("Error processing PDF"):
                return {
                    "is_match": False,
                    "reason": "Unable to extract content from the resume. Please try a different format or input method.",
                    "match_score": "0",
                    "key_strengths": ["N/A"],
                    "missing_skills": ["N/A"],
                    "improvement_suggestions": ["Try using the text input option"]
                }

            formatted_prompt = self.prompt.format(
                resume=resume,
                job_posting=job_posting,
                format_instructions=self.output_parser.get_format_instructions(),
            )

            response = await self.llm.ainvoke(formatted_prompt)
            result = self.output_parser.parse(response.content)

            if "improvement_suggestions" not in result:
                result["improvement_suggestions"] = ["N/A"]

            for key in ["key_strengths", "missing_skills", "improvement_suggestions"]:
                if key in result and isinstance(result[key], list):
                    if len(result[key]) == 1 and isinstance(result[key][0], str) and re.search(r'\d+\.', result[key][0]):
                        items = re.split(r'\s*\d+\.\s*', result[key][0])
                        result[key] = [item.strip() for item in items if item.strip()]

                    result[key] = [re.sub(r'<[^>]+>', '', item) if isinstance(item, str) else item for item in result[key]]

            return result
        except Exception as e:
            return {
                "is_match": False,
                "reason": f"Unable to evaluate match: {str(e)}",
                "match_score": "0",
                "key_strengths": ["N/A"],
                "missing_skills": ["N/A"],
                "improvement_suggestions": ["N/A"]
            }