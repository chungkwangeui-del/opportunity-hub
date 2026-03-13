"use client";

import { useState } from "react";

const FAQ = [
  {
    q: "How often is data updated?",
    a: "Our AI scraper runs daily via GitHub Actions. It checks curated programs, USAJobs and Adzuna APIs, aggregator sites (Pathways to Science, NSF REU Search, Cientifico Latino, ORISE), and Indeed.",
  },
  {
    q: "What fields are covered?",
    a: "We cover Chemistry, Biology, Physics, Computer Science, Engineering, Math, Data Science, Environmental Science, Neuroscience, Materials Science, Biomedical, and Astronomy.",
  },
  {
    q: "Is this free?",
    a: "Yes, completely free. No account needed. OpportunityHub is built to help STEM students find opportunities without barriers.",
  },
  {
    q: "Where do you find opportunities?",
    a: "We track curated programs (ORISE, Microsoft Research, HHMI, Samsung Research, SNU, IBS, and more), plus Pathways to Science, NSF REU Search, ORISE Zintellect, USAJobs, and Adzuna APIs.",
  },
  {
    q: "What locations are covered?",
    a: "We focus on the USA and South Korea. Programs include REUs, national lab internships, government fellowships, Korean research institutes (KAIST, KIST, POSTECH), and more.",
  },
  {
    q: "Can I suggest a source?",
    a: "Absolutely! Open an issue on our GitHub repository with the URL and description of the source you'd like us to add.",
  },
];

function Accordion({ q, a, id }: { q: string; a: string; id: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-gray-200">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-5 text-left"
        aria-expanded={open}
        aria-controls={`faq-${id}`}
      >
        <span className="font-semibold text-gray-900">{q}</span>
        <span className={`ml-4 text-xl text-gray-400 transition-transform ${open ? "rotate-45" : ""}`}>+</span>
      </button>
      {open && <p id={`faq-${id}`} className="pb-5 text-sm leading-relaxed text-gray-600">{a}</p>}
    </div>
  );
}

export default function AboutContent() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold text-gray-900">About OpportunityHub</h1>
      <p className="mt-4 text-lg leading-relaxed text-gray-600">
        OpportunityHub is an AI-powered platform that aggregates STEM opportunities
        for college students worldwide. Every day, our scraper collects research positions,
        internships, fellowships, scholarships, competitions, conferences, summer programs,
        and co-ops from dozens of trusted sources — so you never miss a deadline.
      </p>
      <p className="mt-3 text-lg leading-relaxed text-gray-600">
        Whether you&apos;re a freshman looking for your first lab experience or a graduate student
        seeking a prestigious fellowship, OpportunityHub helps you find the right fit.
      </p>

      <p className="mt-6 text-base font-medium text-gray-700">
        Made by <strong className="text-gray-900">Kwangui Chung</strong> (UIUC student).
      </p>

      <div className="mt-12 rounded-xl border border-gray-200 bg-white p-8">
        <h2 className="mb-2 text-xl font-bold text-gray-900">Tech Stack</h2>
        <ul className="space-y-1 text-sm text-gray-600">
          <li><strong>Scraper:</strong> Python + BeautifulSoup + Firecrawl + Gemini AI</li>
          <li><strong>Database:</strong> Supabase (PostgreSQL)</li>
          <li><strong>Frontend:</strong> Next.js 16 + Tailwind CSS</li>
          <li><strong>Deployment:</strong> Vercel + GitHub Actions (daily cron)</li>
        </ul>
      </div>

      <h2 className="mb-4 mt-16 text-xl font-bold text-gray-900">FAQ</h2>
      <div className="rounded-xl border border-gray-200 bg-white px-6">
        {FAQ.map((item, i) => (
          <Accordion key={i} q={item.q} a={item.a} id={String(i)} />
        ))}
      </div>
    </div>
  );
}
