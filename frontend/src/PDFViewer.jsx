import {useState, useEffect} from "react";
import {Document, Page, pdfjs} from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString()

export default function PDFViewer({fileUrl, setPageNumber, pageNumber}){
    const [numPages, setNumPages]=useState(null);
    const [goToPage, setGoToPage]=useState(1);
    const [loadError, setLoadError]=useState("");
    useEffect(()=>{
        setGoToPage(String(pageNumber))
    },[pageNumber]);
    return (
        <>
        <div className="w-full">
            
            <Document
            file={{url:fileUrl,
                withCredentials:true
            }}
            onLoadSuccess={({numPages})=>setNumPages(numPages)}
            onLoadError={(error)=>{
                setLoadError(error.status);
            }}
            suspense={false}
            loading={
                <div className="mx-auto">
                    <p
                    className="text-center mt-4"
                    >
                        Loading document...
                    </p>
                </div>
            }
            error={
                <div className="mx-auto text-center mt-4">
                    {loadError===404 && "File not found."}
                    {loadError===500 && "Unable to retrieve the document."}
                    {loadError===401 && "Please log in to view this document."}
                </div>
            }
            >
                <div
                className="flex items-center gap-4 justify-center"
                >
                    <button
                    disabled={pageNumber<=1}
                    onClick={()=>setPageNumber(p=>p-1)}
                    >
                        Previous
                    </button>
                    <form
                    className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm"
                    onSubmit={(event)=>{
                        event.preventDefault();
                        const requestedPage=Number(goToPage);
                        if (Number.isInteger(requestedPage) && requestedPage>=1 && requestedPage<=numPages){
                            setPageNumber(requestedPage);
                        }
                    }}
                    >
                        <input
                            id="go-to-page"
                            type="number"
                            min="1"
                            max={numPages ?? 1}
                            step="1"
                            required
                            value={goToPage}
                            onChange={(event)=>setGoToPage(event.target.value)}
                            disabled={!numPages}
                            className="w-12 rounded-md border border-slate-200 px-2 py-1 text-center text-sm font-medium outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 disabled:opacity-50"
                        />
                    </form>
                    <button
                    disabled={pageNumber>=numPages}
                    onClick={()=>setPageNumber(p=>p+1)}
                    >
                        Next
                    </button>
                </div>
                <Page 
                pageNumber={pageNumber}
                width={800}
                ></Page>
                
            </Document>
        </div>
        </>
    )
}