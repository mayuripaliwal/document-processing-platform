from pydantic import BaseModel, EmailStr, Field
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

class UserAccount(BaseModel):
    """
    A valid user account model with valid email and minimum 8 char length password
    """
    email:EmailStr
    password:str=Field(min_length=8)

MAX_FILE_READ_BYTES=1048576

class LocalFileStorage():
    """
    Supports save method to upload a document to local storage
    """
    def __init__(self, upload_dir: Path):
        self.upload_dir=upload_dir.resolve()

    def save(self,file:BinaryIO, filename:str)->str:
        """
        Saves a file locally and returns its storage key.
        """
        if not filename or Path(filename).name!=filename:
            raise ValueError("Invalid filename")

        self.upload_dir.mkdir(parents=True,exist_ok=True)

        storage_key=f"{uuid4().hex}{Path(filename).suffix.lower()}"
        
        destination=self.upload_dir/storage_key

        try:
            file.seek(0)

            with destination.open("xb") as output:
                while True:
                    chunk=file.read(MAX_FILE_READ_BYTES)
                    
                    if not chunk:
                        break
                    
                    output.write(chunk)

            return storage_key
        except Exception:
            #TODO: add logging later
            destination.unlink(missing_ok=True)
            raise
    
    def delete(self, storage_key:str)->None:
        """
        Deletes a stored file using its storage key
        """

        if not storage_key or Path(storage_key).name!=storage_key:
            raise ValueError("Invalid storage key")

        destination=self.upload_dir/storage_key
        destination.unlink(missing_ok=True)