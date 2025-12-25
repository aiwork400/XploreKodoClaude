"""
Quiz API Endpoints
Quiz creation, submission, and grading
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import uuid
from typing import List

from models.quiz import QuizCreate, QuizResponse, QuizRecord, QuizSubmission, QuizAttemptResponse, QuizAttemptRecord
from config.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])

# In-memory quiz storage (will be replaced with database later)
quizzes_db = {}
quiz_attempts_db = {}


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    admin_user: dict = Depends(require_admin)
):
    """
    Create a quiz for a lesson (admin only)
    
    - Only admins can create quizzes
    - Quiz contains multiple choice questions
    - Each question has 4 options and one correct answer
    """
    quiz_id = str(uuid.uuid4())
    
    new_quiz = QuizRecord(
        quiz_id=quiz_id,
        lesson_id=quiz_data.lesson_id,
        title=quiz_data.title,
        questions=quiz_data.questions,
        created_at=datetime.utcnow()
    )
    
    quizzes_db[quiz_id] = new_quiz
    
    return QuizResponse(
        quiz_id=new_quiz.quiz_id,
        lesson_id=new_quiz.lesson_id,
        title=new_quiz.title,
        questions=new_quiz.questions,
        created_at=new_quiz.created_at
    )


@router.get("/lesson/{lesson_id}", response_model=List[QuizResponse])
async def get_quizzes_for_lesson(lesson_id: str):
    """
    Get all quizzes for a specific lesson
    
    - Returns list of quizzes for the lesson
    - Public endpoint (no auth required)
    """
    lesson_quizzes = [
        QuizResponse(
            quiz_id=quiz.quiz_id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            questions=quiz.questions,
            created_at=quiz.created_at
        )
        for quiz in quizzes_db.values()
        if quiz.lesson_id == lesson_id
    ]
    
    return lesson_quizzes


@router.post("/{quiz_id}/submit", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmission,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit quiz answers and get graded
    
    - Authenticated users can submit quiz answers
    - Automatic grading based on correct answers
    - Returns score as percentage
    """
    # Get quiz
    quiz = quizzes_db.get(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Validate answer count
    if len(submission.answers) != len(quiz.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(quiz.questions)} answers, got {len(submission.answers)}"
        )
    
    # Grade the quiz
    correct_count = 0
    for i, question in enumerate(quiz.questions):
        if submission.answers[i] == question.correct_answer:
            correct_count += 1
    
    total_questions = len(quiz.questions)
    score = int((correct_count / total_questions) * 100)
    
    # Create attempt record
    attempt_id = str(uuid.uuid4())
    user_id = current_user.get("user_id")
    
    new_attempt = QuizAttemptRecord(
        attempt_id=attempt_id,
        quiz_id=quiz_id,
        user_id=user_id,
        answers=submission.answers,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_count,
        submitted_at=datetime.utcnow()
    )
    
    quiz_attempts_db[attempt_id] = new_attempt
    
    return QuizAttemptResponse(
        attempt_id=new_attempt.attempt_id,
        quiz_id=new_attempt.quiz_id,
        user_id=new_attempt.user_id,
        score=new_attempt.score,
        total_questions=new_attempt.total_questions,
        correct_answers=new_attempt.correct_answers,
        submitted_at=new_attempt.submitted_at
    )


@router.get("/my-attempts", response_model=List[QuizAttemptResponse])
async def get_my_quiz_attempts(current_user: dict = Depends(get_current_user)):
    """
    Get current user's quiz attempt history
    
    - Returns all quiz attempts for the authenticated user
    - Shows scores and timestamps
    """
    user_id = current_user.get("user_id")
    
    user_attempts = [
        QuizAttemptResponse(
            attempt_id=attempt.attempt_id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            score=attempt.score,
            total_questions=attempt.total_questions,
            correct_answers=attempt.correct_answers,
            submitted_at=attempt.submitted_at
        )
        for attempt in quiz_attempts_db.values()
        if attempt.user_id == user_id
    ]
    
    return user_attempts
