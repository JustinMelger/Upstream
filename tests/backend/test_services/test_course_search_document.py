from backend.database.models import CourseRecord
from backend.services.course_search_document import build_course_search_document


def test_build_course_search_document_includes_course_fields_and_reviews():
    course = CourseRecord(
        id=1,
        title=" FastAPI tutorial ",
        description=" Build APIs with FastAPI. ",
        learning_outcomes="Design endpoints",
        prerequisites="Python basics",
        language="English",
        provider="FastAPI Docs",
        category="Backend",
        level="Beginner",
        duration_hours=3.0,
        url="https://fastapi.tiangolo.com/tutorial/",
        created_at=None,
        created_by="admin",
    )

    out = build_course_search_document(
        course=course,
        review_texts=[" Great practical guide ", "", "Covers testing well"],
        recommendation_count=2,
        recommendation_notes=["Must read before joining API squad"],
        recommended_by=["alice", "bob"],
    )

    assert "FastAPI tutorial" in out
    assert "Build APIs with FastAPI." in out
    assert "Design endpoints" in out
    assert "Python basics" in out
    assert "English" in out
    assert "Great practical guide" in out
    assert "Covers testing well" in out
    assert "recommended 2 times" in out
    assert "recommended_by alice bob" in out
    assert "Must read before joining API squad" in out


def test_build_course_search_document_skips_empty_values():
    course = CourseRecord(
        id=2,
        title="Course A",
        description="",
        learning_outcomes=None,
        prerequisites=None,
        language=None,
        provider=None,
        category=None,
        level=None,
        duration_hours=None,
        url=None,
        created_at=None,
        created_by=None,
    )

    out = build_course_search_document(course=course, review_texts=["  ", "Useful"])
    assert out == "Course A\nUseful"
