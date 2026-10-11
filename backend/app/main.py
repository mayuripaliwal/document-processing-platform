from fastapi import FastAPI, HTTPException, status, Depends, Response, Request, UploadFile, File
import httpx
from app.schemas import UserAccount
from argon2 import PasswordHasher
from fastapi.concurrency import run_in_threadpool
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, DocumentStatus, Document
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete
from argon2.exceptions import VerifyMismatchError
import jwt
import os
from datetime import datetime,timedelta,timezone
from jwt import InvalidTokenError, ExpiredSignatureError
from app.schemas import LocalFileStorage
from pathlib import Path

JWT_SECRET_KEY=os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM="HS256"

IS_PRODUCTION=True if os.environ["ENVIRONMENT"]=="production" else False

FILE_STORAGE_DIR=Path("uploads")

app=FastAPI()

ph=PasswordHasher()

local_storage=LocalFileStorage(FILE_STORAGE_DIR)

async def get_user(request:Request)->int:
    """
    - Dependency function for APIs that require authentication
    - Returns user id from the JWT access token
    - If no token or token is expired or invalid - raises 401 
    """
    jwt_access_token=request.cookies.get("access_token")
    
    if jwt_access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in."
        )
    try:
        payload=await run_in_threadpool(decode_access_token,jwt_access_token)
        user_id=payload["sub"]
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired."
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token."
        )

    return int(user_id)   

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
            detail="Email does not exist"
        )

    user_id,password_hash=user_details

    is_valid_password=await run_in_threadpool(verifyPassword,password_hash,user.password)

    if not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
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

@app.post('/documents',status_code=status.HTTP_201_CREATED)
#TODO add file upload size limit, file type checking
async def postDocument(file:UploadFile= File(...),user_id:int=Depends(get_user),db=Depends(get_db)):
    """
    - Stores the given file for the given user
    - Returns 401 when user is Unauthorized
    - Returns 500 when document upload fails
    """
    #1. Check if user exists
    #2. try to save the file
    #3. if not successful, handle exception
    #4. if successful, save the document in db
    #5. if db save is not successful, remove the document from storage and return 500
    #6. if db save is successful return 201.

    user_exists= await userExists(user_id,db)
    
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account does not exist."
        )
    
    try:
        storage_key=await run_in_threadpool(local_storage.save,file.file,file.filename)
        storage_path=str(local_storage.upload_dir/storage_key)
    except Exception as save_document_exception:
        #TODO add logging here
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document."
        ) from save_document_exception
    try:
        await createDocument(
            user_id=user_id,
            file_name=file.filename,
            stored_file_name=storage_key,
            mime_type="application/pdf",
            file_size=file.size,
            storage_path=storage_path,
            document_status=DocumentStatus.UPLOADED,
            db=db
            )
    except Exception as DocumentInsertException:
        
        #if db write is unsuccesful, remove the stored file
        try:
            await run_in_threadpool(local_storage.delete, storage_key)
            
        except Exception as AttemptDocumentDeleteException:
            #TODO add logging here later - document delete failed; after failed document insert in db
            pass

        #TODO: implement logging later to log DocumentInsertException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document."
        ) from DocumentInsertException
        
    return {
        "message":"Document successfuly uploaded."
    }

@app.get('/documents',status_code=status.HTTP_200_OK)
async def getDocuments(user_id:int=Depends(get_user),db=Depends(get_db)):
    """
    - Fetches all documents for a given user ID
    - If none, returns empty list
    - If invalid user, returns 401
    """
    # Verify user
    user_exists=await userExists(user_id,db)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account does not exist."
        )
    # fetch user's documents
    # fetch documents should return empty list when no documents found
    # else return documents
    documents=await fetchDocuments(user_id,db)

    return {
        "documents":documents
    }

@app.delete('/documents/{document_id}', status_code=status.HTTP_204_NO_CONTENT)
async def deleteDocument(document_id:int, user_id:int=Depends(get_user),db=Depends(get_db)):
    """
    - Given a document_id, deletes a document for a authenticated user
    - If user not authenticated, returns 401
    - If document not found or user not authorized, returns 404
    - If delete unsuccessful, returns 500
    """
    # delete document by id
    # delete actual file from storage,
    # and then it should delete from db, 
    # if document deletion fails, return 500
    # if user is not authorized return 404

    # In case of document deletion failure,if file gets deleted,
    # but its meta data was not deleted, 500 is returned. 
    # If deletion is attempted again and db deletion is successful, 204 is returned.
    
    storage_key=await findDocumentbyID(document_id, user_id, db)
    if storage_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
    try:
        await run_in_threadpool(local_storage.delete,storage_key)
    except (ValueError, OSError) as Value_OS_ERROR:
        #TODO: add logging here later
        # case when file couldnt be deleted
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document deletion failed."
        ) from Value_OS_ERROR
    try:
        is_deleted=await deleteDocumentByID(document_id, user_id, db)
    except Exception as exc:
        #TODO: add logging here later
        # case when file already deleted, but its meta data remains in db
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document deletion failed."
        ) from exc
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    

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

def create_access_token(user_id:int)->str:
    """
    JWT encodes a given user_id and returns a JWT access token with expiry time of 15 minutes
    """
    expire=datetime.now(timezone.utc)+timedelta(minutes=15)

    payload={
        "sub":str(user_id),
        "exp":expire
    }

    return jwt.encode(payload=payload,key=JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)

def decode_access_token(token:str)->dict:
    """
    Decodes a JWT access token and returns the payload {"sub":sub,"exp":exp}
    """
    return jwt.decode(jwt=token,key=JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])

async def userExists(user_id:int,db:AsyncSession)->bool:
    """
    - Db helper which returns true when a User ID exists in Users
    """
    result=await db.execute(
        select(User.id).where(User.id==user_id)
    )

    user_id=result.scalar_one_or_none()

    if user_id is None:
        return False

    return True

async def createDocument(user_id:int,file_name:str, stored_file_name:str,mime_type:str,
    file_size:int,storage_path:str,document_status:DocumentStatus,db:AsyncSession)->Document:
    """
    - Returns newly created document
    - Creates a document in Documents
    - If unsuccessful, transaction is rolled back and any exceptions are raised

    """
    new_document=Document(
        user_id=user_id,
        file_name=file_name,
        stored_file_name=stored_file_name,
        mime_type=mime_type,
        file_size=file_size,
        storage_path=storage_path,
        document_status=document_status
    )

    
    db.add(new_document)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise 

    return new_document

async def fetchDocuments(user_id:int, db:AsyncSession)->list[dict]:
    """
    Returns {`id`,`file_name`, `file_size`, `created_at`} for each document belonging to a given user_id
    """
    result=await db.execute(
        select(Document.id, Document.file_name,Document.file_size,Document.created_at)
        .where(Document.user_id==user_id)
        .order_by(Document.created_at.desc())
    )

    return result.mappings().all()

async def findDocumentbyID(document_id:int, user_id:int, db:AsyncSession)-> str | None:
    """
    - Db helper which returns storage_key for given document_id of a user
    - If not found, returns None
    """
    result=await db.execute(select(Document.stored_file_name)
    .where(Document.user_id==user_id, Document.id==document_id))

    storage_key=result.scalar_one_or_none()

    return storage_key

async def deleteDocumentByID(document_id:int, user_id:int, db:AsyncSession)->bool:
    """
    - Deletes document by id from DB 
    - if document deletion fails, raise Exception
    - if user is not authorized or document does not exist return False
    - if deletion successful returns True
    """

    try:
        result=await db.execute(delete(Document)
        .where(Document.id==document_id, Document.user_id==user_id))
        
        if result.rowcount==0:
            await db.rollback()
            return False

        await db.commit()
        return True
    except Exception:
        await db.rollback()
        raise
