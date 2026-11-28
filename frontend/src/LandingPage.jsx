import {Link} from "react-router-dom";
import { useState } from 'react'
import { Dialog, DialogPanel } from '@headlessui/react'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Demo Video', href: '#demo' },
  { name: 'Features', href: '#features' },
  { name: 'About', href: '#about' },
]
const features = [
  {
    title: "AI-Powered Question Answering",
    description: "Ask questions about your uploaded PDFs and get contextual answers based on their content."
  },
  {
    title: "Find Answers in Your PDF",
    description: "Click a citation to navigate to the relevant PDF page, and QueryPDF will automatically highlight the corresponding content."
  },
  {
    title: "PDF Uploads & Management",
    description: "Upload PDF files up to 10 MB, view and delete your documents, and track their processing status. Ask up to 10 questions per day."
  },
  {
    title: "Hybrid Search",
    description: "Combines meaning-based search with keyword matching to find relevant information."
  },
  {
    title: "Background Processing",
    description: "Documents are processed in the background, so uploading and preparing PDFs doesn't block the main application."
  },
  {
    title:"Processing Status Tracking",
    description:"Follow each document through its processing journey: Uploaded, Processing, and Completed."
  }
];

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="">
      <header className="absolute inset-x-0 top-0 z-50">
        <nav aria-label="Global" className="flex items-center justify-between p-6 lg:px-8">
          <div className="flex lg:flex-1">
            <Link
            to="/"
            className="text-xl text-gray-900"
          >
            Query<span className="text-blue-600">PDF</span>
          </Link>
          </div>
          <div className="flex lg:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-gray-500"
            >
              <span className="sr-only">Open main menu</span>
              <Bars3Icon aria-hidden="true" className="size-6" />
            </button>
          </div>
          <div className="hidden lg:flex lg:gap-x-12">
            {navigation.map((item) => (
              <a key={item.name} href={item.href} className="text-sm/6 font-semibold text-gray-900">
                {item.name}
              </a>
            ))}
          </div>
          <div className="hidden lg:flex lg:flex-1 lg:justify-end">
            <Link
            to="/login"
            className="flex gap-1 justify items-center rounded-md text-sm font-semibold text-gray-900"
          >
            Log in
            <span aria-hidden="true">&rarr;</span>
          </Link>
          </div>
        </nav>
        <Dialog open={mobileMenuOpen} onClose={setMobileMenuOpen} className="lg:hidden">
          <div className="fixed inset-0 z-50" />
          <DialogPanel className="bg-white fixed inset-y-0 right-0 z-50 w-full overflow-y-auto p-6 sm:max-w-sm sm:ring-1 sm:ring-gray-900/10">
            <div className="flex items-center justify-between">
              <Link
                to="/"
                className="text-xl text-gray-900"
              >
                Query<span className="text-blue-600">PDF</span>
              </Link>
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="-m-2.5 rounded-md p-2.5 text-gray-700"
              >
                <span className="sr-only">Close menu</span>
                <XMarkIcon aria-hidden="true" className="size-6" />
              </button>
            </div>
            <div className="mt-6 flow-root">
              <div className="-my-6 divide-y divide-gray-500/10">
                <div className="space-y-2 py-6">
                  {navigation.map((item) => (
                    <a
                      key={item.name}
                      href={item.href}
                      onClick={()=>setMobileMenuOpen(false)}
                      className="-mx-3 block rounded-lg px-3 py-2 text-base/7 font-semibold text-gray-900 hover:bg-gray-50"
                    >
                      {item.name}
                    </a>
                  ))}
                </div>
                <div className="py-6">
                  <Link
                    to="/login"
                    className="flex gap-1 justify items-center rounded-md text-sm font-semibold text-gray-900"
                  >
                    Log in
                    <span aria-hidden="true">&rarr;</span>
                  </Link>
                </div>
              </div>
            </div>
          </DialogPanel>
        </Dialog>
      </header>

      <div className="relative isolate min-h-screen overflow-hidden pt-14">
        <div
          aria-hidden="true"
          className="absolute inset-x-0 -top-16 -z-10 flex transform-gpu justify-center overflow-hidden blur-3xl"
        >
          <div
            style={{
              clipPath:
                'polygon(73.6% 51.7%, 91.7% 11.8%, 100% 46.4%, 97.4% 82.2%, 92.5% 84.9%, 75.7% 64%, 55.3% 47.5%, 46.5% 49.4%, 45% 62.9%, 50.3% 87.2%, 21.3% 64.1%, 0.1% 100%, 5.4% 51.1%, 21.4% 63.9%, 58.9% 0.2%, 73.6% 51.7%)',
            }}
            className="aspect-1318/752 w-329.5 flex-none bg-linear-to-r from-[#9fd6fc] to-[#8680fd] opacity-50"
          />
        </div>
        <div className="relative z-10 pt-24 sm:pt-32 lg:pb-40">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="grid mx-auto max-w-7xl items-center gap-16 lg:grid-cols-2">
              {/**CTA */}
              <div className="max-w-2xl">
                <h1 className="text-5xl font-semibold tracking-tight text-balance text-gray-900 sm:text-7xl">
                  Ask questions from your documents
                </h1>
                <p className="mt-8 text-lg font-medium text-pretty text-gray-500 sm:text-xl/8">
                  Upload PDF files and get answers with citations from your own sources.
                </p>
                <div className="mt-10 flex items-left justify-left gap-x-6">
                  <Link
                    to="/signup"
                    className="relative z-10 rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                  >
                    Get started
                  </Link>
                  <a
                    href="#demo"
                    className="relative z-10 rounded-md border border-gray-900 px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-xs hover:bg-blue-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                  >
                    Watch Demo
                  </a>
                </div>
              </div>

              {/**Demo Screenshot */}
              <img
                alt="App screenshot"
                src="/Ask_Documents_Screenshot.png"
                width={2432}
                height={1442}
                className="h-auto w-full rounded-xl shadow-xl ring-1 ring-gray-900/10"
              />
            </div>
          </div>
        </div>
      </div>
      {/**Video Demo */}
      <section className="relative z-10 px-6 sm:py-8">
        <div className="mx-auto max-w-7xl">
          <div  id="demo" className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-semibold tracking-tight text-gray-900 sm:text-4xl">
              See QueryPDF in action
            </h2>

            <p className="mt-4 text-lg text-gray-600">
              Watch how you can upload a PDF, ask questions, and navigate
              directly to cited sources.
            </p>
          </div>

          <div className="mx-auto mt-12 max-w-5xl overflow-hidden rounded-xl bg-gray-900 shadow-xl ring-1 ring-gray-900/10">
            <video
              controls
              preload="metadata"
              playsInline
              className="h-auto w-full"
              poster="/QueryPDF_Demo_Screenshot.png"
            >
              <source src="/QueryPDF_Video_Demo.mp4" type="video/mp4" />
              Your browser does not support the video element.
            </video>
          </div>

          <p className="mt-4 text-center text-sm text-gray-500">
            20-second demonstration using a <a
            href="https://s22.q4cdn.com/513010314/files/doc_financials/2022/q4/r/MGM-Resorts-Exhibit-99.1.pdf"
            className="underline text-blue-600"
            target="_blank"
            rel="noopener noreferrer"
            >sample</a> financial report.
          </p>
        </div>
      </section>
      {/**Features */}
      <section id="features" className="mx-auto max-w-7xl px-6 pt-10 lg:px-8 lg:pt-4">
        <h2 className="text-center text-3xl font-semibold tracking-tight text-gray-900">
          Features
        </h2>

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(function(feature,index){
            return(
            <article key={feature.title}
            className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
            >
              <h3 className="text-lg font-semibold text-gray-900">
                {feature.title}
              </h3>

              <p className="mt-3 text-sm leading-6 text-gray-600">
                {feature.description}
              </p>
            </article>
            )
          })}
        </div>
      </section>
      <footer id="about" className="px-6 mt-20">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 py-6 text-sm text-gray-500 sm:flex-row lg:px-8 py-1">
          <p>
            Built with ❤️ by <a 
              href="https://github.com/mayuripaliwal"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-indigo-600 hover:text-indigo-500 hover:underline"
            > 
              Mayuri Paliwal
            </a>
          </p>
          <a 
            href="https://github.com/mayuripaliwal/document-processing-platform"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-indigo-600 hover:text-indigo-500 hover:underline"
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  )
}
