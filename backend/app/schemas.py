from pydantic import BaseModel, EmailStr, Field
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4
from fastapi import UploadFile

class UserAccount(BaseModel):
    """
    A valid user account model with valid email and minimum 8 char length password
    """
    email:EmailStr
    password:str=Field(min_length=8)


class FileTooLargeError(Exception):
    """
    File size exceeds maximum allowed size
    """
    pass
class InvalidFileNameError(Exception):
    """
    File does not have a valid file name
    """
    pass
class LocalFileStorage():
    """
    - Supports save method to upload a document to local storage
    - Supports delete method to delete a document from local storage
    """
    def __init__(self, upload_dir: Path):
        self.upload_dir=upload_dir.resolve()
        self._MAX_FILE_SIZE_BYTES=10485760
        self._MAX_FILE_READ_BYTES=1048576

    def getMaxFileSize(self)->int:
        """
        Returns max file size that is permissible.
        """
        return self._MAX_FILE_SIZE_BYTES

    def isValidFileSize(self,file:UploadFile)->bool:
        """
        - Returns if a file has a permissible file size
        """
        return file.size is not None and file.size <= self._MAX_FILE_SIZE_BYTES

    def isValidFileType(self,file:UploadFile)->bool:
        """
        Returns if a file has a valid file type
        """
        return (
            file.filename is not None
            and file.content_type=="application/pdf"
        )

    def save(self,file:BinaryIO, filename:str)->str:
        """
        - Saves a file locally and returns its storage key.
        - Also enforces file size check while reading, and raises ValueError when size exceeds
        maximum permissible file size
        """
        if not filename or Path(filename).name!=filename:
            raise InvalidFileNameError("Invalid filename")

        self.upload_dir.mkdir(parents=True,exist_ok=True)

        storage_key=f"{uuid4().hex}{Path(filename).suffix.lower()}"
        
        destination=self.upload_dir/storage_key

        try:
            file.seek(0)
            file_bytes_read=0

            with destination.open("xb") as output:
                while True:
                    chunk=file.read(self._MAX_FILE_READ_BYTES)
                    
                    if not chunk:
                        break

                    if len(chunk)+file_bytes_read>self._MAX_FILE_SIZE_BYTES:
                        raise FileTooLargeError("File exceeds maximum allowed size")
                    
                    file_bytes_read+=len(chunk)
                    output.write(chunk)

            return storage_key
        except Exception:
            #TODO: add logging later
            destination.unlink(missing_ok=True)
            raise
    
    def delete(self, storage_key:str)->None:
        """
        - Deletes a stored file using its storage key
        - If storage_key is invalid, raises Value Error
        - No exception is raised if file does not exist but storage_key is valid
        """

        if not storage_key or Path(storage_key).name!=storage_key:
            raise ValueError("Invalid storage key")

        destination=self.upload_dir/storage_key
        destination.unlink(missing_ok=True)