"""Debug test to verify database setup"""
import pytest
import uuid
from decimal import Decimal
from db_models.aiml_training import AIMLCourseDB


def test_debug_database_connection(test_db, client):
    """Debug: Check if test data exists"""
    
    # Create a course directly in the test
    course = AIMLCourseDB(
        course_id=uuid.uuid4(),
        course_name="Debug Test Course",
        level=1,
        track="debug",
        duration_weeks=4,
        price=Decimal("100.00"),
        description="Debug course",
        is_active=True
    )
    test_db.add(course)
    test_db.commit()
    
    # Check data in test_db directly
    direct_count = test_db.query(AIMLCourseDB).count()
    print(f"\n🔍 Direct test_db query: {direct_count} courses")
    
    # Check via API
    response = client.get("/api/aiml/courses")
    print(f"🔍 API response status: {response.status_code}")
    api_data = response.json()
    api_count = len(api_data)
    print(f"🔍 API query: {api_count} courses")
    
    if api_count > 0:
        print(f"🔍 First course from API: {api_data[0]['course_name']}")
    
    # They should match!
    assert direct_count > 0, f"No data in test DB! Count: {direct_count}"
    assert api_count > 0, f"API returned no data! Count: {api_count}"
    assert direct_count == api_count, f"Mismatch! DB has {direct_count} but API returned {api_count}"
