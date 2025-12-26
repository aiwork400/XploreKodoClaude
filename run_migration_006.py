"""
Run migration 006: Add wallet and coaching system tables
"""
from config.database import engine, Base
from db_models.wallet import (
    UserWallet, 
    WalletTransaction, 
    VoiceCoachingSession,
    VideoSession,
    AssessmentResult
)

def run_migration():
    print("Creating coaching system tables...")
    Base.metadata.create_all(engine, tables=[
        UserWallet.__table__,
        WalletTransaction.__table__,
        VoiceCoachingSession.__table__,
        VideoSession.__table__,
        AssessmentResult.__table__
    ])
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()

