import {AUTH_STATUSES} from "./AuthConfig";
import {useState} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';

export default function AskDocuments({setAuthStatus, documentId, setPageNumber}){
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const MAX_QUERY_LENGTH = 200;
    
    const [loading, setLoading]=useState(false);

    const [query, setQuery]=useState("");

    const [answer, setAnswer] = useState(null);

    const [searchError, setSearchError]=useState("");

    async function handleSearch(event){
        event.preventDefault();
        setLoading(true);
        try {
            const response = await fetch(`${BACKEND_URL}/documents/${documentId}/search/?query=${encodeURIComponent(query.trim())}`,{
                method:"GET",
                credentials:"include",
                headers:{
                    "Content-Type":"application/json"
                }
            });

            if (!response.ok){
                if (response.status===401){
                    setAuthStatus(AUTH_STATUSES.LOGGED_OUT);
                    setAnswer(null);
                }
                else if (response.status===503){
                    setSearchError("Ask Documents is unavailable at the moment. Please try again later.")
                    setAnswer(null);
                }
                else if (response.status===404){
                    setSearchError("We could not find what you were looking for.");
                    setAnswer(null);
                }
                else{
                    setSearchError("Something went wrong. Please try again.")
                    setAnswer(null);
                }
            }
            else{
                const result= await response.json();
                setAnswer(result);
                setSearchError("");
            }
        }
        catch(error){
            console.log(error);
            setSearchError("Unable to connect to the server. Please try again.");
            setAnswer(null);
        }
        finally{
            setLoading(false);
        }
    }
    return (
        <main
        className="mt-4 ml-8 mr-8 mx-auto"
        >
        <header className="mb-8 text-center">
            <div className="mb-4 text-4xl">✦</div>

            <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                Ask your documents
            </h1>

            <p className="mt-3 text-gray-500">
                Find answers from your uploaded PDFs using AI.
            </p>
        </header>
        {/* Search form */}
        <form
            onSubmit={handleSearch}
            className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm"
        >
            <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Ask a question about your documents..."
                maxLength={MAX_QUERY_LENGTH}
                rows={3}
                className="w-full resize-y border-0 bg-transparent p-2 text-gray-800 outline-none placeholder:text-gray-400 focus:ring-0"
            />

            <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                <span className="text-xs text-gray-400">
                    {query.length}/{MAX_QUERY_LENGTH} characters
                </span>

                <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    {loading ? "Searching..." : "Search →"}
                </button>
            </div>
        </form>
        {searchError && !loading && (
            <p
            className="text-red-600 text-center text-sm"
            >
                {searchError}
            </p>
        )}
        {/* Answer */}
            {!loading && answer && answer.length>0 && (
                <section className="mt-8 mb-8">
                    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                        <div className="mb-4 flex items-center gap-2">
                            <span className="text-xl text-blue-600">✦</span>
                            <h2 className="text-lg font-semibold text-gray-900">
                                Answer
                            </h2>
                        </div>

                        <div
                        className="prose prose-gray max-w-none leading-7"
                        >  
                            {answer.map((part, index)=>(
                                <div key={index}>
                                <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                >
                                    {part.answer_part}
                                </ReactMarkdown>
                                
                                {part.citations.length>0 &&(
                                    <div>
                                        {part.citations.map(({page_no, section_title}, index)=>(
                                            <span>
                                                <button
                                                key={index}
                                                onClick={()=> setPageNumber(Number(page_no))}
                                                className="text-sm rounded-lg bg-blue-100 m-1 p-1 hover:bg-blue-200"
                                                >Page: {page_no} ⋅ {section_title}
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                )}
                                </div>
                            ))}                             
                               
                        </div>
                    </div>
                </section>
            )}
        </main>
    )
}
