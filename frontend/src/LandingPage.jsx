import { ArrowRightIcon } from '@heroicons/react/24/outline'
import {Link} from "react-router-dom";

export default function LandingPage() {
  return (
    <>
    <div className="relative isolate min-h-screen overflow-hidden bg-white">
      <div className="relative z-10 backdrop-blur-[1px] flex items-center justify-between px-10 py-8">
      <Link
        to="/"
        className="text-xl text-gray-900"
      >
        Query<span className="text-blue-600">PDF</span>
      </Link>
      <Link
        to="/login"
        className="flex gap-1 justify items-center rounded-md text-sm font-semibold text-gray-900"
      >
        Log in
        <span aria-hidden="true">&rarr;</span>
      </Link>
    </div>
      <svg
        aria-hidden="true"
        className="absolute inset-0 z-0 size-full stroke-blue-300"
      >
        <defs>
          <pattern
            x="50%"
            y={-1}
            id="0787a7c5-978c-4f66-83c7-11c213f99cb7"
            width={50}
            height={50}
            patternUnits="userSpaceOnUse"
          >
            <path d="M50 0V50H0" fill="none" />
          </pattern>
        </defs>
        <rect fill="url(#0787a7c5-978c-4f66-83c7-11c213f99cb7)" width="100%" height="100%" strokeWidth={0} />
      </svg>
      <div className="mx-auto max-w-7xl px-6 pt-10 pb-24 sm:pb-32 lg:flex lg:px-8 lg:py-40">
        
        <div className="mx-auto max-w-2xl lg:mx-0 lg:shrink-0 lg:pt-8">
          <div className="mt-3 sm:mt-4 lg:mt-2">
            
          </div>
          <h1 className="relative z-10 bg-white/30 text-5xl font-semibold tracking-tight text-pretty text-gray-900 sm:text-7xl">
            Ask questions from your personal knowledge base
          </h1>
          <p className="relative z-10 bg-white/30 mt-8 text-lg font-medium text-pretty text-gray-600 sm:text-xl/8">
            Upload your notes as PDF files and get answers with citations from your own sources.
          </p>
          <div className="mt-10 flex items-center gap-x-6">
            <Link
              to="/signup"
              className="relative z-10 rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
            >
              Get started
            </Link>
          </div>
        </div>
        <div className="mx-auto mt-16 flex max-w-2xl sm:mt-24 lg:mt-0 lg:mr-0 lg:ml-10 lg:max-w-none lg:flex-none xl:ml-32">
          <div className="max-w-3xl flex-none sm:max-w-5xl lg:max-w-none">
            <div className="-m-2 rounded-xl bg-gray-900/5 p-2 ring-1 ring-gray-900/10 ring-inset lg:-m-4 lg:rounded-2xl lg:p-4">
              {/**TODO: Add screenshot here */}
              
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  )
}
