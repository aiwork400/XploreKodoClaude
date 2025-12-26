"""
Cost Configuration for Coaching Platform
Defines pricing constants for voice coaching, video sessions, and assessments
"""
from decimal import Decimal

# Voice Coaching Costs (per minute)
VOICE_COACHING_PRACTICE_COST_PER_MINUTE = Decimal("5.00")  # NPR per minute
VOICE_COACHING_ASSESSMENT_COST_PER_MINUTE = Decimal("7.50")  # NPR per minute
VOICE_COACHING_LIVE_COST_PER_MINUTE = Decimal("10.00")  # NPR per minute

# Voice Coaching Mode Costs (per minute)
VOICE_COACHING_STANDARD_COST_PER_MINUTE = Decimal("2.00")  # NPR per minute (Standard mode)
VOICE_COACHING_REALTIME_COST_PER_MINUTE = Decimal("40.00")  # NPR per minute (Realtime mode)

# Video Session Costs (per minute)
VIDEO_SESSION_COST_PER_MINUTE = Decimal("15.00")  # NPR per minute

# Assessment Costs (one-time)
ASSESSMENT_PRONUNCIATION_COST = Decimal("50.00")  # NPR
ASSESSMENT_FLUENCY_COST = Decimal("50.00")  # NPR
ASSESSMENT_COMPREHENSION_COST = Decimal("50.00")  # NPR
ASSESSMENT_OVERALL_COST = Decimal("100.00")  # NPR

# Minimum session durations (minutes)
MIN_VOICE_SESSION_DURATION = 5
MIN_VIDEO_SESSION_DURATION = 10

# Maximum session durations (minutes)
MAX_VOICE_SESSION_DURATION = 60
MAX_VIDEO_SESSION_DURATION = 120

# Topup bonus tiers
TOPUP_BONUS_TIER_1_AMOUNT = Decimal("1000.00")  # NPR
TOPUP_BONUS_TIER_1_PERCENTAGE = Decimal("10.00")  # 10%

TOPUP_BONUS_TIER_2_AMOUNT = Decimal("2000.00")  # NPR
TOPUP_BONUS_TIER_2_PERCENTAGE = Decimal("20.00")  # 20%

