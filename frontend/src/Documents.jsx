import {useEffect, useState} from 'react';
import {AUTH_STATUSES} from "./AuthConfig";
import UploadDocument from "./UploadDocument";

export function formatFileSize(file_size_bytes){
    if (file_size_bytes>=1024*1024){
        return `${(file_size_bytes / (1024*1024)).toFixed(2)} MB`;
    }
    if (file_size_bytes>=1024){
        return `${(file_size_bytes / (1024)).toFixed(2)} KB`;
    }
    return `${file_size_bytes} B`;
}
export default function Documents({setAuthStatus}){
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const [documents, setDocuments] =useState([]);

    const [hasNewDocument, setHasNewDocument]=useState(false);

    function formatDate(given_date){
        const date=new Date(given_date);
        return date.toLocaleDateString();
    }

    async function getUserDocuments(){
        try{
            const response=await fetch(`${BACKEND_URL}/documents`,{
                method:"GET",
                credentials:"include",
                headers:{
                    "Content-Type":"application/json"
                }
            });

            if (!response.ok){
                if (response.status===401){
                    setAuthStatus(AUTH_STATUSES.LOGGED_OUT);
                }
                console.log(response);
            }
            else{
                const result=await response.json();
                console.log(result);
                setDocuments(result["documents"])
            }
        }
        catch(error){
            {/**TODO: display to user that their documents ccould not be fetched,and 
                where documents.length===0, fix that conditional 
                to only show when no fetch document error message is present */}
            console.log(error);
        }
        finally{

        }
    }

    useEffect(()=>{
        getUserDocuments()
    },[hasNewDocument])

    return (
        <div
        className="flex-col"
        >
        {documents.length===0 && (
            <p
            className="mt-4 text-center text-5xl text-gray-900"
            >
                No documents here...
            </p>
        )
        }
        <div className="mt-10 min-h-full flex-col justify-center items-start mr-10">
            <UploadDocument setHasNewDocument={setHasNewDocument} setAuthStatus={setAuthStatus}></UploadDocument>
        
        {/**#TODO: add pagination later */}
        {documents.length>0 && (
            
            <div
            className="mx-auto"
            >
            <ul
            className="divide-y divide-gray-200"
            >
                <li className="grid grid-cols-3 gap-4 bg-gray-50 py-3 text-sm font-semibold text-gray-600">
                    <span>Document</span>
                    <span>File Size</span>
                    <span>Date Uploaded</span>
                </li>
                {documents.map((document)=>(
                    <li 
                    key={document.id}
                    className="grid grid-cols-3 items-center gap-4 py-4 hover:bg-gray-100"
                    >
                        <span
                        className="truncate font-medium text-gray-600"
                        >
                            {document.file_name}
                        </span>
                        <span
                        className="text-sm text-gray-600"
                        >
                            {formatFileSize(document.file_size_bytes)}
                        </span>
                        <span
                        className="text-sm text-gray-600"
                        >   
                            {formatDate(document.created_at)}
                        </span>
                    </li>

                ))}
            </ul>
            </div>
        )}
        </div>
        </div>
    )
}