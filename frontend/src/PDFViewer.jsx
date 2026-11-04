import {useState} from "react";
import {Document, Page, pdfjs} from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString()

export default function PDFViewer({fileUrl}){
    const [numPages, setNumPages]=useState(null);
    const [pageNumber, setPageNumber]=useState(1);
    return (
        <div>
            <Document
            file={{url:fileUrl,
                withCredentials:true
            }}
            onLoadSuccess={({numPages})=>setNumPages(numPages)}
            >
                <Page pageNumber={pageNumber}></Page>
            </Document>
        </div>
    )
}