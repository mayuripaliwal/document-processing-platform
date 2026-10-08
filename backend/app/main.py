from fastapi import FastAPI, HTTPException, status, Depends, Response
import httpx
from app.schemas import UserAccount
from argon2 import PasswordHasher
from fastapi.concurrency import run_in_threadpool
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from argon2.exceptions import VerifyMismatchError
import jwt
import os
from datetime import datetime,timedelta,timezone

JWT_SECRET_KEY=os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM="HS256"

IS_PRODUCTION="production" if os.environ["ENVIRONMENT"]=="production" else False

app=FastAPI()

ph=PasswordHasher()

@app.get('/')
async def home():
    return {
        "message":"Backend is working"
    }

@app.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(user:UserAccount,db:AsyncSession=Depends(get_db)):
    """
    Creates a new account with given email address and password.
    If account already exists for the given email address, returns 409 Conflict
    """

    password_hash=await run_in_threadpool(hashPassword,user.password)

    try:
        await createUser(user.email,password_hash,db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    return {
        "message":"Account created successfully."
    }

@app.post('/login',status_code=status.HTTP_200_OK)
async def login(user:UserAccount,response:Response, db:AsyncSession=Depends(get_db)):
    """
    - Authenticate user with password verification
    - Stores JWT access token in http-Only Cookie
    """
    user_details=await getUserByEmail(user.email,db)

    if user_details is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user_id,password_hash=user_details

    is_valid_password=await run_in_threadpool(verifyPassword,password_hash,user.password)

    if not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    jwt_access_token=await run_in_threadpool(create_access_token,user_id)

    response.set_cookie(
        key="access_token",
        value=jwt_access_token,
        httponly=True,
        secure=True if IS_PRODUCTION else False,
        samesite="lax"
    )

    return {
        "message":"User logged in successfully."
    }

def verifyPassword(password_hash:str,password:str)->bool:
    """
    Verify a password against a stored password hash
    """
    try:
        return ph.verify(password_hash,password)
    except VerifyMismatchError:
        return False

def hashPassword(password:str):
    """
    Hashes password using argon2-cffi
    """

    password_hash=ph.hash(password)

    return password_hash

async def createUser(email:str,password_hash:str,db:AsyncSession):
    """
    Db helper to create a new user with email and password hash.
    If account already exists, raises exception and rolls back transaction
    """

    new_user=User(
        email=email,
        password_hash=password_hash
    )

    async with db.begin():
        db.add(new_user)

    return new_user

async def getUserByEmail(email:str,db:AsyncSession):
    """
    - Db helper to fetch user_id,password_hash from a given email
    - Returns none when email does not exist
    """

    result=await db.execute(
        select(User.id,User.password_hash).where(User.email==email)
    )

    user=result.one_or_none()

    if user is None:
        return None

    return user

def create_access_token(user_id:int):
    """
    JWT encodes a given user_id and returns a JWT access token with expiry time of 15 minutes
    """
    expire=datetime.now(timezone.utc)+timedelta(minutes=15)

    payload={
        "sub":str(user_id),
        "exp":expire
    }

    return jwt.encode(payload=payload,key=JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)