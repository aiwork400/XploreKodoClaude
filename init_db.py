"""
Initialize Database Tables
Creates all tables in PostgreSQL database
"""
from config.database import Base, engine
from db_models.user import UserDB
from db_models.lesson import LessonDB
from db_models.progress import ProgressDB
from db_models.payment import PaymentDB
from db_models.enrollment import EnrollmentDB
from db_models.quiz import QuizDB, QuizAttemptDB
from db_models.certificate import CertificateDB


def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully!")


if __name__ == "__main__":
    init_db()
