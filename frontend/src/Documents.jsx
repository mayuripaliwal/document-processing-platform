import {useEffect, useState, useCallback} from 'react';
import {AUTH_STATUSES} from "./AuthConfig";
import UploadDocument from "./UploadDocument";
import {TrashIcon} from '@heroicons/react/24/outline';
import PDFViewer from "./PDFViewer";
import {Link} from "react-router-dom";

export function formatFileSize(file_size_bytes){
    if (file_size_bytes>=1024*1024){
        return `${(file_size_bytes / (1024*1024)).toFixed(2)} MB`;
    }
    if (file_size_bytes>=1024){
        return `${(file_size_bytes / (1024)).toFixed(2)} KB`;
    }
    return `${file_size_bytes} B`;
}
const DOCUMENT_STATUS_POLLING_DURATION_MS =  3000;
export default function Documents({setAuthStatus}){
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const [documents, setDocuments] =useState([]);

    const [newUpload, setNewUpload]=useState(0);

    const [loadingDocuments, setLoadingDocuments]=useState(false);

    const [getUserDocumentsError, setGetDocumentsError]=useState("");

    const [deleteDocumentsError, setDeleteDocumentsError]=useState("");

    const [offset, setOffset] = useState(0);

    const [total, setTotal] = useState(0);

    const [hasMore, setHasMore] = useState(false);

    const PAGE_SIZE = 10;


    function formatDate(given_date){
        const date=new Date(given_date);
        return date.toLocaleDateString();
    }

    const getUserDocuments=useCallback(async()=>{
        setGetDocumentsError("");
        setDeleteDocumentsError("");
        setLoadingDocuments(true);
        try{
            const response=await fetch(`${BACKEND_URL}/documents?limit=${PAGE_SIZE}&offset=${offset}`,{
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
                else {
                    setGetDocumentsError("Something went wrong. Please try again.");
                }
                return null;
            }
            else{
                const result=await response.json();
                setDocuments(result["documents"]);
                setTotal(result["total"]);
                setHasMore(result["hasMore"]);
                return result["documents"];
            }
        }
        catch(error){
            setGetDocumentsError("Unable to connect to the server. Please try again.");
            return null;
        }
        finally{
            setLoadingDocuments(false);
        }
    },[BACKEND_URL, setAuthStatus, offset]);

    {/**This use effect is for updating documents whenever a new document is uploaded 
    or when fetching next page  */}
    useEffect(()=>{
        getUserDocuments()
    },[newUpload])

    {/**This use effect is for polling document status */}
    useEffect(()=>{
        const hasPendingDocuments=documents.some(
            document=>document.document_status==="UPLOADED" ||
            document.document_status==="PROCESSING"
        );
        if (!hasPendingDocuments) return;

        let timeoutId;
        let cancelled = false;
        
        async function pollDocuments(){
            const latestDocuments = await getUserDocuments();
            if (cancelled) return;

            const shouldContinue = latestDocuments===null || latestDocuments.some(
                document=>document.document_status==="UPLOADED" ||
                document.document_status==="PROCESSING"
            );

            if (shouldContinue){
                timeoutId=setTimeout(pollDocuments, DOCUMENT_STATUS_POLLING_DURATION_MS);
            }
        }

        timeoutId=setTimeout(pollDocuments, DOCUMENT_STATUS_POLLING_DURATION_MS);

        return () => {
            cancelled = true;
            clearTimeout(timeoutId);
        }
    },[documents, getUserDocuments])

    async function handleDeleteDocument(documentId) {
        setDeleteDocumentsError("");
        try {
            const response = await fetch(`${BACKEND_URL}/documents/${documentId}`,{
                method: "DELETE",
                credentials: "include",
            });

            if (!response.ok) {
                if (response.status===401){
                    setAuthStatus(AUTH_STATUSES.LOGGED_OUT);
                }
                else {
                    setDeleteDocumentsError("Unable to delete document. Please try again.");
                }
            }
            else{
                await getUserDocuments();
            }
        } catch (error) {
            setDeleteDocumentsError("Unable to connect to the server. Please try again.")
        }
    }

    return (
        <div
        className="flex-col w-full"
        >
        {getUserDocumentsError && documents.length===0 && !loadingDocuments &&(
            <p
            className="mt-4 text-center text-lg text-red-600"
            >
                {getUserDocumentsError}
            </p>
        )}
        <div className="mt-10 min-h-full flex-col justify-center items-start mr-10">
            <UploadDocument setNewUpload={setNewUpload} setAuthStatus={setAuthStatus}></UploadDocument>
        {documents.length===0 && !loadingDocuments && !getUserDocumentsError && (
            <p
            className="mt-4 text-center text-xl text-gray-600"
            >
                Nothing to show here.
            </p>
        )
        }
        {deleteDocumentsError  && !loadingDocuments &&(
            <p
            className="mt-4 text-center text-lg text-red-600"
            >
                {deleteDocumentsError}
            </p>
        )}
        {documents.length>0 && (
            
            <div
            className="mx-auto ml-4"
            >
            <ul
            className="divide-y divide-gray-200"
            >
                <li className="grid grid-cols-5 gap-4 bg-gray-50 py-3 text-sm font-semibold text-gray-600">
                    <span>Document</span>
                    <span>File Size</span>
                    <span>Date Uploaded</span>
                    <span>Status</span>
                    <span>Delete</span>
                </li>
                {documents.map((document)=>(
                    <li 
                    key={document.id}
                    className="grid grid-cols-5 items-center gap-4 py-4 hover:bg-gray-100"
                    >
                        <Link
                        to={`/documents/${document.id}`}
                        className="truncate font-medium text-gray-600"
                        >
                            {document.file_name}
                        </Link>
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
                        <span
                        className="text-sm text-gray-600"
                        >   
                            {document.document_status}
                        </span>
                        <span
                        >
                        <button
                        onClick={()=>handleDeleteDocument(document.id)}
                        >
                            <TrashIcon
                            className="w-6 h-6 text-red-600"
                            />
                        </button>
                        </span>
                    </li>

                ))}
            </ul>
            
            <div className="mt-6 flex items-center justify-center gap-4">
                <button
                    disabled={offset === 0 || loadingDocuments}
                    onClick={() => setOffset(offset - PAGE_SIZE)}
                    className="text-sm text-blue-600 disabled:text-gray-400 hover:text-blue-800 hover:bg-blue-100 disabled:hover:bg-transparent rounded-lg p-1"
                >
                    ← Previous
                </button>

                <span className="text-sm text-gray-600">
                    Page {1+(offset / PAGE_SIZE)} of {Math.ceil(total / PAGE_SIZE)}
                </span>

                <button
                    disabled={!hasMore || loadingDocuments}
                    onClick={() => setOffset(offset + PAGE_SIZE)}
                    className="text-sm text-blue-600 disabled:text-gray-400 hover:text-blue-800 hover:bg-blue-100 disabled:hover:bg-transparent rounded-lg p-1"
                >
                    Next →
                </button>
            </div>

            </div>
                
    )
        }
        </div>
        </div>
    )
}