import asyncio
import sys
from app import main
import pytest
from app.schemas import LocalFileStorage
from sqlalchemy.exc import SQLAlchemyError

if sys.platform=="win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
def create_user(client,email:str,password:str):
    """
    - Helper to create a User in db
    - Returns POST /signup API response
    """
    return client.post(
        '/signup',
        json={
            "email":email,
            "password":password
        }
    )
def login_user(client,email:str,password:str):
    """
    - Helper to login a User in db.
    - User must exist before calling login.
    - Returns POST /login API response
    """
    return client.post(
        '/login',
        json={
            "email":email,
            "password":password
        }
    )

def create_document(client):
    """
    - Helper to create a mock document with name `test_pdf`
    """
    pdf_content=b"%PDF-1.\n Test PDF Content\n%%EOF"
    return client.post('/documents',files={
        "file":("test_pdf",pdf_content,"application/pdf")
    })
def test_signup(client):
    """
    - Test sign up is successful - 201
    - Test sign up with duplicate sign up is unsuccessful with status code - 409
    """
    assert create_user(client,"test@example.com","stringst").status_code==201

    assert create_user(client,"test@example.com","stringst").status_code==409

def test_login(client):
    """
    - Test login is successful - 200
    - Test login with wrong password - 401
    - Test login with wrong email - 401
    """

    assert create_user(client,"test@example.com","stringst").status_code==201

    response=login_user(client,"test@example.com","stringst")

    assert response.status_code==200

    assert response.cookies.get("access_token") is not None

    response=login_user(client,"test@example.com","wrong_password")

    assert response.status_code==401

    response=login_user(client,"wrong_email@example.com","stringst")

    assert response.status_code==401


def test_post_document(client, tmp_path, monkeypatch):
    """
    - Test document upload is successful - 201
    - Test unauthenticated document upload fails with - 401
    """
    monkeypatch.setattr(main,"local_storage",LocalFileStorage(tmp_path))
    pdf_content=b"%PDF-1.\n Test PDF Content\n%%EOF"

    response=client.post('/documents',files={
        "file":("test.pdf",pdf_content,"application/pdf")
    })
    
    assert response.status_code==401

    saved_files=list(tmp_path.iterdir())
    
    assert len(saved_files)==0

    assert create_user(client,"test@example.com","stringst").status_code==201

    assert login_user(client,"test@example.com","stringst").status_code==200    

    response=client.post('/documents',files={
        "file":("test.pdf",pdf_content,"application/pdf")
    })

    assert response.status_code==201

    saved_files=list(tmp_path.iterdir())

    assert len(saved_files)==1

    assert saved_files[0].read_bytes()==pdf_content

def test_failed_post_document(client, tmp_path, monkeypatch):
    """
    - Tests failed document mocking failed db write and returns 500
    - Tests that created file is deleted
    """
    assert create_user(client,"test@example.com","stringst").status_code==201
    
    assert login_user(client,"test@example.com","stringst").status_code==200

    monkeypatch.setattr(main,"local_storage",LocalFileStorage(tmp_path))

    async def fail_create_document(**kwargs):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(main,"createDocument", fail_create_document)

    failed_response=create_document(client)

    assert failed_response.status_code==500

    saved_files=list(tmp_path.iterdir())
    
    assert len(saved_files)==0

def test_failed_save_document(client, tmp_path, monkeypatch):
    """
    - Tests failed document mocking file write error and returns 500
    """
    assert create_user(client,"test@example.com","stringst").status_code==201
    
    assert login_user(client,"test@example.com","stringst").status_code==200
    
    monkeypatch.setattr(main,"local_storage",LocalFileStorage(tmp_path))
    pdf_content=b"%PDF-1.\n Test PDF Content\n%%EOF"

    def fail_save_document(file,filename):
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(main.local_storage,"save", fail_save_document)

    failed_response=client.post('/documents',files={
        "file":("test.pdf",pdf_content,"application/pdf")
    })

    assert failed_response.status_code==500

    saved_files=list(tmp_path.iterdir())
    
    assert len(saved_files)==0

def test_get_document(client,monkeypatch, tmp_path):
    """
    - Tests that unauthenticated access returns 401
    - Tests that a user can see all their documents 
    - Tests that a user can only see their documents
    """
    monkeypatch.setattr(main,"local_storage",LocalFileStorage(tmp_path))

    # Tests that unauthenticated access returns 401
    
    response=client.get('/documents')

    assert response.status_code==401

    # Tests that a user can see all their documents 

    assert create_user(client,"test@example.com","stringst").status_code==201
    
    assert login_user(client,"test@example.com","stringst").status_code==200

    response=client.get('/documents')

    assert response.status_code==200

    data=response.json()

    assert "documents" in data

    assert len(data["documents"])==0    

    response= create_document(client)

    assert response.status_code==201
    
    response=client.get('/documents')
    
    assert response.status_code==200

    data=response.json()

    assert "documents" in data

    assert len(data["documents"])==1 

    documents=data["documents"]

    assert len(documents[0])==4

    assert documents[0]["file_name"]=="test_pdf"

    # Tests that a user can only see their documents

    assert create_user(client,"another_user@example.com","stringst").status_code==201
        
    assert login_user(client,"another_user@example.com","stringst").status_code==200

    response=client.get('/documents')

    assert response.status_code==200

    data=response.json()

    assert "documents" in data

    assert len(data["documents"])==0

def test_delete_document(client,monkeypatch, tmp_path):
    """
    - Test successful document deletion
    - Test successful response even in case of file not exist on storage but exist in db
    - Test storage file deletion error
    """
    monkeypatch.setattr(main,"local_storage",LocalFileStorage(tmp_path))

    # Test successful document deletion

    assert create_user(client,"another_user@example.com","stringst").status_code==201
            
    assert login_user(client,"another_user@example.com","stringst").status_code==200

    response = create_document(client)

    assert response.status_code==201

    documents=list(tmp_path.iterdir())
    
    assert len(documents)==1

    document_id=1
    
    response=client.delete(f'/documents/{document_id}')

    assert response.status_code==204

    documents=list(tmp_path.iterdir())

    assert len(documents)==0

    # Test successful response even in case of file not exist on storage but exist in db

    response = create_document(client)
    
    assert response.status_code==201

    documents=list(tmp_path.iterdir())
    
    assert len(documents)==1

    documents[0].unlink()

    assert list(tmp_path.iterdir())==[]

    document_id=2
    
    response=client.delete(f'/documents/{document_id}')

    assert response.status_code==204

    documents=list(tmp_path.iterdir())

    assert len(documents)==0

    response=client.delete(f'/documents/{document_id}')
    
    assert response.status_code==404

    ## Test storage file deletion error

    response = create_document(client)
        
    assert response.status_code==201

    documents=list(tmp_path.iterdir())
    
    assert len(documents)==1

    document_id=3

    def fail_delete_document(storage_key):
        raise OSError("Failed to delete document")

    monkeypatch.setattr(main.local_storage,"delete", fail_delete_document)

    response=client.delete(f'/documents/{document_id}')
        
    assert response.status_code==500

    
def test_delete_db_document(client,tmp_path,monkeypatch):
    """
    - Test db file metadata deletion error
    """
    monkeypatch.setattr(main,"local_storage",LocalFileStorage(tmp_path))
    
    assert create_user(client,"another_user@example.com","stringst").status_code==201
            
    assert login_user(client,"another_user@example.com","stringst").status_code==200

    response = create_document(client)
            
    assert response.status_code==201

    documents=list(tmp_path.iterdir())
    
    assert len(documents)==1

    document_id=1

    async def fail_delete_document_db(**kwargs):
        raise SQLAlchemyError("Failed to delete document from db")

    monkeypatch.setattr(main,"deleteDocumentByID", fail_delete_document_db)

    response=client.delete(f'/documents/{document_id}')
        
    assert response.status_code==500