from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from decouple import config
import uvicorn

# Configuration
SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here-change-in-production-INSECURE-DEFAULT")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# App initialization
app = FastAPI(
    title="Voice of SiYuan",
    description="A private campus forum for XJTUers",
    version="0.1.0"
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory database (for MVP)
users_db = {}
posts_db = []
comments_db = []
next_post_id = 1
next_comment_id = 1

# Models
class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Post(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    author: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)

class Comment(BaseModel):
    id: Optional[int] = None
    post_id: int
    content: str = Field(..., min_length=1, max_length=1000)
    author: str
    created_at: datetime = Field(default_factory=datetime.now)

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if username in users_db:
        user_dict = users_db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@app.get("/")
async def root():
    return {
        "message": "Welcome to Voice of SiYuan - XJTU Campus Forum",
        "version": "0.1.0 MVP"
    }

@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "disabled": False
    }
    users_db[user.username] = user_dict
    return User(**user_dict)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/posts", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_active_user)
):
    global next_post_id
    new_post = Post(
        id=next_post_id,
        title=post.title,
        content=post.content,
        author=current_user.username,
        created_at=datetime.now(timezone.utc)
    )
    posts_db.append(new_post.model_dump())
    next_post_id += 1
    return new_post

@app.get("/posts", response_model=List[Post])
async def get_posts(skip: int = 0, limit: int = 10):
    return posts_db[skip : skip + limit]

@app.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: int):
    for post in posts_db:
        if post["id"] == post_id:
            return post
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Post not found"
    )

@app.put("/posts/{post_id}", response_model=Post)
async def update_post(
    post_id: int,
    post_update: PostCreate,
    current_user: User = Depends(get_current_active_user)
):
    for i, post in enumerate(posts_db):
        if post["id"] == post_id:
            if post["author"] != current_user.username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this post"
                )
            posts_db[i]["title"] = post_update.title
            posts_db[i]["content"] = post_update.content
            posts_db[i]["updated_at"] = datetime.now(timezone.utc)
            return posts_db[i]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Post not found"
    )

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user)
):
    for i, post in enumerate(posts_db):
        if post["id"] == post_id:
            if post["author"] != current_user.username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this post"
                )
            posts_db.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Post not found"
    )

@app.post("/posts/{post_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment: CommentCreate,
    current_user: User = Depends(get_current_active_user)
):
    global next_comment_id
    # Check if post exists
    post_exists = any(post["id"] == post_id for post in posts_db)
    if not post_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    new_comment = Comment(
        id=next_comment_id,
        post_id=post_id,
        content=comment.content,
        author=current_user.username,
        created_at=datetime.now(timezone.utc)
    )
    comments_db.append(new_comment.model_dump())
    next_comment_id += 1
    return new_comment

@app.get("/posts/{post_id}/comments", response_model=List[Comment])
async def get_comments(post_id: int):
    post_comments = [c for c in comments_db if c["post_id"] == post_id]
    return post_comments

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
