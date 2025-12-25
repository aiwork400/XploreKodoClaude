"""
Stripe Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

def get_stripe_key() -> str:
    """Get Stripe secret key from environment"""
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise ValueError(
            "STRIPE_SECRET_KEY not found in environment variables. "
            "Please set it in .env file or environment."
        )
    return stripe_key
