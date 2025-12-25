from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.lessons import router as lessons_router
from api.progress import router as progress_router
from api.payments import router as payments_router
from api.enrollments import router as enrollments_router
from api.quizzes import router as quizzes_router
from api.i18n import router as i18n_router
from api.ai_widget import router as ai_widget_router
from api.certificates import router as certificates_router
from api.dashboard import router as dashboard_router
from api.japanese_training import router as japanese_training_router
from api.aiml_training import router as aiml_training_router

app = FastAPI(
    title="XploraKodo API",
    description="""
## Japanese Language Learning Platform API

XploraKodo is a comprehensive Japanese language learning platform with JLPT-focused content.

### Features:
* **Authentication**: User registration and JWT-based login
* **Lesson Management**: CRUD operations for Japanese lessons (N5-N1)
* **Progress Tracking**: Track user progress through lessons
* **Payment Integration**: Stripe payment processing
* **Enrollments**: Enroll in and manage lesson access
* **Quizzes**: Take quizzes with automatic grading
* **Certificates**: Generate certificates for completed lessons
* **Dashboard**: View comprehensive user statistics

### Authentication:
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Roles:
* **Student**: Can view lessons, track progress, take quizzes, earn certificates
* **Admin**: Can create/edit/delete lessons and quizzes
    """,
    version="1.0.0",
    contact={"name": "XploraKodo Support", "email": "support@xplorakodo.com"},
    license_info={"name": "MIT License"}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(lessons_router)
app.include_router(progress_router)
app.include_router(payments_router)
app.include_router(enrollments_router)
app.include_router(quizzes_router)
app.include_router(certificates_router)
app.include_router(dashboard_router)
app.include_router(japanese_training_router)
app.include_router(aiml_training_router)
app.include_router(i18n_router)
app.include_router(ai_widget_router)

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {"message": "Welcome to XploraKodo API"}





