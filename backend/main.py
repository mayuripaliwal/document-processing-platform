from fastapi import FastAPI
import os
from dotenv import load_dotenv
app=FastAPI()


load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")


@app.get('/')
def home():
    return {
        "message":"Backend is working"
    }