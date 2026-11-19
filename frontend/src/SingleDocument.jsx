import {useParams} from "react-router-dom";
import {useState} from "react";
import PDFViewer from "./PDFViewer";
import AskDocuments from "./AskDocuments";

export default function SingleDocument({setAuthStatus}){
    const {documentId}=useParams();
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const fileUrl=`${BACKEND_URL}/documents/${documentId}/file`
    const [pageNumber, setPageNumber]=useState(1);
    return (
        <div
        className="flex w-full min-w-0"
        >
            <div
            className="min-w-0 flex-[2] overflow-auto"
            >
                <PDFViewer fileUrl={fileUrl} pageNumber={pageNumber} setPageNumber={setPageNumber}/>
            </div>
            <div
            className="min-w-0 flex-[2]"
            >
            <AskDocuments documentId={documentId} setAuthStatus={setAuthStatus} setPageNumber={setPageNumber}/>
            </div>
        </div>
    )
}