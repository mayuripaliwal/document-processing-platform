import { DocumentTextIcon } from '@heroicons/react/24/outline';
import {useRef, useState} from "react";
import {formatFileSize} from "./Documents";
import {AUTH_STATUSES} from "./AuthConfig";

export default function UploadDocument({setHasNewDocument, setAuthStatus}) {
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const fileInputRef = useRef(null);
    const MAX_FILE_SIZE_BYTES_PDF=10 * 1024 * 1024;

    const [fileUploadErrorMessage, setFileUploadErrorMessage]=useState("");

    const [uploadingDocument, setUploadingDocument]=useState(false);

    const [selectedFile, setSelectedFile]=useState(null);

    async function handleSelectDocument(){
        fileInputRef.current?.click();
    }
    async function handleUploadDocument(){
        if (!selectedFile) {
            setFileUploadErrorMessage("No file chosen to upload.");
            return;
        }
        try{
            setUploadingDocument(true);
            setFileUploadErrorMessage("");
            const formData=new FormData();
            formData.append("file", selectedFile);

            const response=await fetch(`${BACKEND_URL}/documents`,{
                method:"POST",
                credentials:"include",
                body:formData,    
            });

            if (!response.ok){
                if (response.status===413){
                    setFileUploadErrorMessage("Could not upload file. File size exceeds upload limit")
                }
                else if (response.status===415){
                    setFileUploadErrorMessage("Could not upload file. File is not a valid PDF.")
                }
                else if (response.status===400){
                    setFileUploadErrorMessage("Could not upload file. File name is not valid.")
                }
                else if (response.status===401){
                    setFileUploadErrorMessage("Please login to continue.");
                    setAuthStatus(AUTH_STATUSES.LOGGED_OUT);
                }
                else if (response.status===500){
                    setFileUploadErrorMessage("Unable to upload file. Please try again.");
                }
            }
            else{
                setHasNewDocument(true);
            }
        }
        catch(error){
            setFileUploadErrorMessage("Unable to connect to the server. Please try again.");
        }
        finally{
            setUploadingDocument(true);
        }
    }
  return (
    <>
    <div className="min-w-full px-4">
        <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            hidden
            onChange={(event)=>{
                const file=event.target.files[0];

                if (!file){
                    return;
                }
                if (!file.name.toLowerCase().endsWith(".pdf")){
                    event.target.value="";
                    setSelectedFile(null);
                    setFileUploadErrorMessage("Please select a valid pdf file.");
                    return;
                }
                if (file.size > MAX_FILE_SIZE_BYTES_PDF){
                    event.target.value="";
                    setSelectedFile(null);
                    setFileUploadErrorMessage("File size must not exceed 10 MB.");
                    return;
                }
                setFileUploadErrorMessage("");
                setSelectedFile(file);
            }}
        />
        <button
        type="button"
        onClick={handleSelectDocument}
        className="relative block w-full rounded-lg border-2 border-dashed border-gray-300 p-10 text-center hover:border-indigo-400 focus:outline-2 focus:outline-offset-2 focus:outline-indigo-600"
        >
        <DocumentTextIcon
            aria-hidden="true"
            className="mx-auto size-12 text-indigo-500"
        />

        <span className="mt-2 block text-sm font-semibold text-gray-900">
            {selectedFile ? 
            <>
            <p>{`${selectedFile.name}`}</p>
            <p
            className="mt-1"
            >{`${formatFileSize(selectedFile.size)}`}</p> 
            </>: 
            "Upload a new document"}
        </span>
        </button>
        <button
        className="mt-4 relative block bg-indigo-500 text-gray-100 rounded-lg p-2 border-2 hover:bg-indigo-600 focus:outline-1 focus:outline-offset-1 focus:outline-indigo-600"
        disabled={uploadingDocument}
        onClick={handleUploadDocument}
        >
            Upload Document
        </button>
    </div>
    <p
    className="py-2 text-red-600 text-sm"
    >
        {fileUploadErrorMessage}
    </p>
    </>
  );
}