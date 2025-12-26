"""
Assessment Service
Business logic for evaluating student answers using GPT-4 with rubric-based scoring
"""
import os
import openai
from dotenv import load_dotenv
from typing import Dict
from decimal import Decimal

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class AssessmentService:
    """Service for assessing student answers using AI"""
    
    # Rubric-based prompts for different tracks
    RUBRIC_PROMPTS = {
        "caregiving": """You are an expert Japanese language assessor specializing in caregiving contexts.
Evaluate the student's answer using this rubric:
1. Grammar (0-25 points): Correctness of Japanese grammar and sentence structure
2. Keigo Appropriateness (0-25 points): Proper use of polite/respectful language for caregiving context
3. Contextual Fit (0-25 points): How well the answer fits the caregiving situation
4. Overall Quality (0-25 points): Naturalness, clarity, and effectiveness

Provide scores for each rubric category and overall score (0-100).
Give constructive feedback in 2-3 sentences.""",
        
        "academic": """You are an expert Japanese language assessor specializing in academic contexts.
Evaluate the student's answer using this rubric:
1. Grammar (0-25 points): Correctness of Japanese grammar and sentence structure
2. Keigo Appropriateness (0-25 points): Proper use of honorific language for academic/professional context
3. Contextual Fit (0-25 points): How well the answer fits the academic situation
4. Overall Quality (0-25 points): Formality, clarity, and academic appropriateness

Provide scores for each rubric category and overall score (0-100).
Give constructive feedback in 2-3 sentences.""",
        
        "food_tech": """You are an expert Japanese language assessor specializing in food technology contexts.
Evaluate the student's answer using this rubric:
1. Grammar (0-25 points): Correctness of Japanese grammar and sentence structure
2. Keigo Appropriateness (0-25 points): Proper use of polite language for workplace context
3. Contextual Fit (0-25 points): How well the answer fits the food technology/workplace situation
4. Overall Quality (0-25 points): Clarity, professionalism, and workplace appropriateness

Provide scores for each rubric category and overall score (0-100).
Give constructive feedback in 2-3 sentences."""
    }
    
    @staticmethod
    async def evaluate_answer(
        question_id: str,
        student_answer: str,
        track: str,
        expected_keigo_level: str,
        question_text: str = "",
        question_type: str = "general"
    ) -> Dict:
        """
        Evaluate student answer using GPT-4 with rubric-based scoring
        
        Args:
            question_id: Question identifier
            student_answer: Student's answer
            track: Track context (caregiving, academic, food_tech)
            expected_keigo_level: Expected keigo level (teineigo, sonkeigo, kenjougo)
            question_text: Original question text
            question_type: Type of question (keigo_check, grammar, vocabulary, etc.)
            
        Returns:
            dict with rubric scores, overall score, and feedback
        """
        # Get rubric prompt for track
        rubric_prompt = AssessmentService.RUBRIC_PROMPTS.get(
            track.lower(),
            AssessmentService.RUBRIC_PROMPTS["caregiving"]
        )
        
        # Build assessment prompt
        assessment_prompt = f"""{rubric_prompt}

Question: {question_text}
Expected Keigo Level: {expected_keigo_level}
Question Type: {question_type}

Student Answer: {student_answer}

Evaluate the answer and provide:
1. Grammar score (0-25)
2. Keigo Appropriateness score (0-25)
3. Contextual Fit score (0-25)
4. Overall Quality score (0-25)
5. Overall score (0-100)
6. Feedback text (2-3 sentences)

Respond in JSON format:
{{
    "grammar": <score>,
    "keigo_appropriateness": <score>,
    "contextual_fit": <score>,
    "overall_quality": <score>,
    "overall": <score>,
    "feedback": "<feedback text>"
}}"""
        
        try:
            # Call GPT-4
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Japanese language assessment expert. Always respond with valid JSON."},
                    {"role": "user", "content": assessment_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            assessment_data = json.loads(response_text)
            
            # Validate and format scores
            grammar = float(assessment_data.get("grammar", 0))
            keigo_appropriateness = float(assessment_data.get("keigo_appropriateness", 0))
            contextual_fit = float(assessment_data.get("contextual_fit", 0))
            overall_quality = float(assessment_data.get("overall_quality", 0))
            overall = float(assessment_data.get("overall", 0))
            feedback = assessment_data.get("feedback", "No feedback provided.")
            
            # Ensure scores are in valid ranges
            grammar = max(0, min(25, grammar))
            keigo_appropriateness = max(0, min(25, keigo_appropriateness))
            contextual_fit = max(0, min(25, contextual_fit))
            overall_quality = max(0, min(25, overall_quality))
            overall = max(0, min(100, overall))
            
            return {
                "question_id": question_id,
                "grammar": round(grammar, 2),
                "keigo_appropriateness": round(keigo_appropriateness, 2),
                "contextual_fit": round(contextual_fit, 2),
                "overall_quality": round(overall_quality, 2),
                "overall": round(overall, 2),
                "feedback": feedback,
                "track": track,
                "expected_keigo_level": expected_keigo_level
            }
            
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "question_id": question_id,
                "grammar": 0.0,
                "keigo_appropriateness": 0.0,
                "contextual_fit": 0.0,
                "overall_quality": 0.0,
                "overall": 0.0,
                "feedback": f"Assessment error: Could not parse response. Original: {response_text[:100]}",
                "track": track,
                "expected_keigo_level": expected_keigo_level
            }
        except Exception as e:
            raise Exception(f"Assessment error: {str(e)}")

