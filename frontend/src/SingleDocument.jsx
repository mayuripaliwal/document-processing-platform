import {useParams} from "react-router-dom";
import PDFViewer from "./PDFViewer";
import AskDocuments from "./AskDocuments";

export default function SingleDocument(){
    const {documentId}=useParams();
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const fileUrl=`${BACKEND_URL}/documents/${documentId}/file`
    return (
        <div
        className="flex gap-10 w-full"
        >
            <div>
                <PDFViewer fileUrl={fileUrl}/>
            </div>
            <AskDocuments documentId={documentId}/>
        </div>
    )
}