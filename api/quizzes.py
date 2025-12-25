"""
Quiz Management API - Database Version
Quiz creation and grading with PostgreSQL
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import List, Union, Dict

from models.quiz import QuizCreate, QuizResponse, QuizResultResponse, QuizAttemptResponse
from db_models.quiz import QuizDB, QuizAttemptDB
from config.database import get_db
from config.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a quiz for a lesson (admin only) - stores in PostgreSQL"""
    quiz_id = str(uuid.uuid4())
    
    new_quiz = QuizDB(
        quiz_id=quiz_id,
        lesson_id=quiz_data.lesson_id,
        title=quiz_data.title,
        questions=quiz_data.questions,
        created_at=datetime.utcnow()
    )
    
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    
    return QuizResponse(
        quiz_id=new_quiz.quiz_id,
        lesson_id=new_quiz.lesson_id,
        title=new_quiz.title,
        questions=new_quiz.questions,
        created_at=new_quiz.created_at
    )


@router.get("/lesson/{lesson_id}", response_model=List[QuizResponse])
async def get_quizzes_for_lesson(
    lesson_id: str,
    db: Session = Depends(get_db)
):
    """Get all quizzes for a specific lesson from PostgreSQL"""
    quizzes = db.query(QuizDB).filter(QuizDB.lesson_id == lesson_id).all()
    
    return [
        QuizResponse(
            quiz_id=quiz.quiz_id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            questions=quiz.questions,
            created_at=quiz.created_at
        )
        for quiz in quizzes
    ]


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse, status_code=status.HTTP_201_CREATED)
async def submit_quiz(
    quiz_id: str,
    submission: Dict[str, Union[List[str], Dict[str, str]]],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit quiz answers and get automatic grading from PostgreSQL"""
    
    # Get quiz
    quiz = db.query(QuizDB).filter(QuizDB.quiz_id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    answers = submission.get("answers", [])
    
    # Convert list answers to dict format (index-based)
    if isinstance(answers, list):
        answers_dict = {str(i): ans for i, ans in enumerate(answers)}
    else:
        answers_dict = answers
    
    # Grade the quiz
    total_questions = len(quiz.questions)
    correct_answers = 0
    
    for i, question in enumerate(quiz.questions):
        correct_answer = question.get("correct_answer")
        user_answer = answers_dict.get(str(i))
        
        if user_answer == correct_answer:
            correct_answers += 1
    
    score = round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0
    
    # Save attempt (store as dict for consistency)
    attempt_id = str(uuid.uuid4())
    
    new_attempt = QuizAttemptDB(
        attempt_id=attempt_id,
        quiz_id=quiz_id,
        user_id=current_user["user_id"],
        answers=answers_dict,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_answers,
        submitted_at=datetime.utcnow()
    )
    
    db.add(new_attempt)
    db.commit()
    db.refresh(new_attempt)
    
    return QuizResultResponse(
        attempt_id=new_attempt.attempt_id,
        quiz_id=new_attempt.quiz_id,
        score=new_attempt.score,
        total_questions=new_attempt.total_questions,
        correct_answers=new_attempt.correct_answers,
        submitted_at=new_attempt.submitted_at
    )


@router.get("/my-attempts", response_model=List[QuizAttemptResponse])
async def get_my_quiz_attempts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all quiz attempts for current user from PostgreSQL"""
    attempts = db.query(QuizAttemptDB).filter(
        QuizAttemptDB.user_id == current_user["user_id"]
    ).all()
    
    return [
        QuizAttemptResponse(
            attempt_id=attempt.attempt_id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            score=attempt.score,
            total_questions=attempt.total_questions,
            correct_answers=attempt.correct_answers,
            submitted_at=attempt.submitted_at
        )
        for attempt in attempts
    ]
