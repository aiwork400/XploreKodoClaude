"""
Authentication API Endpoints
User registration and login
"""
from fastapi import APIRouter, HTTPException, status
import bcrypt
from datetime import datetime
import uuid

from models.user import UserCreate, UserResponse, LoginRequest, TokenResponse, UserInDB
from config.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# In-memory user storage (will be replaced with database later)
users_db = {}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_user_by_email(email: str) -> UserInDB | None:
    """Get user from database by email"""
    for user in users_db.values():
        if user.email == email:
            return user
    return None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    new_user = UserInDB(
        user_id=user_id,
        email=user_data.email,
        role=user_data.role,
        password_hash=hashed_password,
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    users_db[user_id] = new_user
    
    return UserResponse(
        user_id=new_user.user_id,
        email=new_user.email,
        role=new_user.role
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: LoginRequest):
    """Login user and return JWT token"""
    user = get_user_by_email(login_data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.user_id, "role": user.role}
    )
    
    return TokenResponse(access_token=access_token, token_type="bearer")
