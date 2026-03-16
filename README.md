# OpportunityHub

AI-powered STEM opportunity aggregator for college students (USA and South Korea). Research positions, internships, fellowships, scholarships, and more — updated daily from dozens of trusted sources.

## Architecture

```
Scraper (Python) → Supabase (PostgreSQL) → Web Portal (Next.js)
```

- **Scraper**: Collects from curated programs, USAJobs, Adzuna, The Muse, JSearch, aggregator sites (Pathways to Science, NSF REU, ORISE, Cientifico Latino), and Indeed. Uses Gemini for extraction, Firecrawl for dynamic pages.
- **Database**: Supabase stores opportunities with deduplication by URL.
- **Web Portal**: Next.js app for browsing, filtering, and bookmarking.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project
- API keys: Gemini, Firecrawl (required); USAJobs, Adzuna, The Muse, JSearch (optional)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/chungkwangeui-del/opportunity-hub.git
cd opportunity-hub
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
```

**Required:**
- `GEMINI_API_KEY` — Google AI Studio
- `FIRECRAWL_API_KEY` — Firecrawl
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key

**Optional (scraper skips if not set):**
- `USAJOBS_API_KEY`, `USAJOBS_EMAIL`
- `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`
- `THE_MUSE_API_KEY`
- `RAPIDAPI_KEY` (for JSearch)

### 3. Scraper

```bash
pip install -r requirements.txt
python scraper.py
```

### 4. Web portal

```bash
cd web-portal
cp .env.example .env.local
# Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Deployment

- **Web**: Vercel (connect GitHub repo)
- **Scraper**: GitHub Actions runs daily at 9:00 AM EST (`daily-scrape.yml`)

## Project structure

```
opportunity-hub/
├── scraper.py           # Main scraper
├── curated_programs.json
├── requirements.txt
├── .github/workflows/
│   └── daily-scrape.yml
└── web-portal/          # Next.js app
    └── src/
```

## License

MIT
