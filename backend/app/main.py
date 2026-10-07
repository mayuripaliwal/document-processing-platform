from fastapi import FastAPI, HTTPException, status, Depends
import httpx
from app.schemas import UserCreate
from argon2 import PasswordHasher
from fastapi.concurrency import run_in_threadpool
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from sqlalchemy.exc import IntegrityError

app=FastAPI()

ph=PasswordHasher()

@app.get('/')
async def home():
    return {
        "message":"Backend is working"
    }

@app.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(user:UserCreate,db:AsyncSession=Depends(get_db)):
    """
    Creates a new account with given email address and password.
    If account already exists for the given email address, returns 409 Conflict
    """

    password_hash=await run_in_threadpool(hash_password,user.password)

    try:
        await create_user(user.email,password_hash,db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    return {
        "message":"Account created successfully."
    }

def hash_password(password:str):
    """
    Hashes password using argon2-cffi
    """

    password_hash=ph.hash(password)

    return password_hash

async def create_user(email:str,password_hash:str,db:AsyncSession):
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