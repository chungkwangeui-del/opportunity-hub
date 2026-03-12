import os
import json
import time
import re
import logging
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from firecrawl import Firecrawl

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("OpportunityHub")

# ---------------------------------------------------------------------------
# Curated Programs — open to ALL students (not school-specific), exact deadlines
# ---------------------------------------------------------------------------
CURATED_PROGRAMS: list[dict] = [
    # ── USA Research / REU (open to external students) ───────────────
    {"organization": "Caltech", "title": "SURF – Summer Undergraduate Research Fellowships", "url": "https://sfp.caltech.edu/undergraduate-research/programs/surf", "field": "General STEM", "opportunity_type": "Research", "year_level": ["Freshman", "Sophomore", "Junior"], "country": "USA", "state": "CA", "city": "Pasadena", "is_paid": True, "compensation": "~$7,500 stipend", "deadline": "2026-03-01", "description": "10-week summer research at Caltech. Open to external students. Must secure a Caltech faculty mentor."},
    {"organization": "Stanford", "title": "SURGE – Sustainability Undergraduate Research in Geoscience and Engineering", "url": "https://sustainability.stanford.edu/our-community/access-belonging-community/surge", "field": "Engineering", "opportunity_type": "Summer Program", "year_level": ["Sophomore", "Junior"], "country": "USA", "state": "CA", "city": "Stanford", "is_paid": True, "compensation": "$4,800 stipend + housing + travel (~$14,000 total)", "deadline": "2026-01-11", "description": "8-week fully funded summer research at Stanford. Open to all US undergrads. Welcomes low-income, first-gen, new-to-research students."},
    {"organization": "NASA", "title": "OSTEM Summer Internships", "url": "https://intern.nasa.gov/", "field": "General STEM", "opportunity_type": "Internship", "year_level": ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$7,500–$10,000", "deadline": "2026-02-27", "description": "Paid internships across all NASA centers. Work on real missions. Open to all US citizens with 3.0+ GPA."},
    {"organization": "NASA JPL", "title": "JPL Summer Internship Program", "url": "https://www.jpl.nasa.gov/edu/internships/apply/jpl-summer-internship-program", "field": "General STEM", "opportunity_type": "Internship", "year_level": ["Sophomore", "Junior", "Senior", "Graduate"], "country": "USA", "state": "CA", "city": "Pasadena", "is_paid": True, "compensation": "Stipend + housing/travel allowance", "deadline": "2026-03-13", "description": "10-week summer internship at NASA's Jet Propulsion Laboratory. Robotics, planetary science, data science, engineering."},
    {"organization": "DOE", "title": "SULI – Science Undergraduate Laboratory Internships", "url": "https://science.osti.gov/wdts/suli", "field": "General STEM", "opportunity_type": "Internship", "year_level": ["Sophomore", "Junior", "Senior"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$650/week + $250/week housing", "deadline": "2026-01-07", "description": "10-week research at DOE National Labs (Argonne, Brookhaven, ORNL, etc.). Open to all US citizens/permanent residents."},
    {"organization": "NIH", "title": "SIP – Summer Internship Program in Biomedical Research", "url": "https://www.training.nih.gov/research-training/pb/sip/", "field": "Biology", "opportunity_type": "Research", "year_level": ["Sophomore", "Junior", "Senior"], "country": "USA", "state": "MD", "city": "Bethesda", "is_paid": True, "compensation": "Stipend", "deadline": "2026-02-27", "description": "8–12 week paid summer research at NIH. Open to US citizens/permanent residents age 18+."},
    {"organization": "Amgen Foundation", "title": "Amgen Scholars Program (U.S.)", "url": "https://amgenscholars.com/us-program/", "field": "Biology", "opportunity_type": "Summer Program", "year_level": ["Sophomore", "Junior"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$4,500 stipend + housing", "deadline": "2026-02-01", "description": "8–10 week summer research at top universities (Harvard, MIT, Stanford, etc.). Open to all undergrads. Biomedical focus."},
    {"organization": "Woods Hole Oceanographic Institution", "title": "Summer Student Fellowship", "url": "https://www.whoi.edu/what-we-do/educate/undergraduate-programs/summer-student-fellowship/", "field": "Environmental Science", "opportunity_type": "Research", "year_level": ["Junior", "Senior"], "country": "USA", "state": "MA", "city": "Woods Hole", "is_paid": True, "compensation": "$680/week + housing + travel", "deadline": "2026-02-01", "description": "10–12 week marine science research. Open to all undergrads who have completed junior year. International students welcome."},
    {"organization": "HHMI Janelia", "title": "Cech Fellows – Summer Undergraduate Research", "url": "https://www.janelia.org/you-janelia/students-and-postdocs/janelia-summer-undergraduate-research-program", "field": "Neuroscience", "opportunity_type": "Research", "year_level": ["Junior", "Senior"], "country": "USA", "state": "VA", "city": "Ashburn", "is_paid": True, "compensation": "Stipend + housing + travel", "deadline": "2025-12-22", "description": "9-week summer research at HHMI Janelia. ~20 fellows. Open to US citizens and visa holders at any US institution."},
    {"organization": "Georgia Tech", "title": "Physics REU", "url": "https://physicsreu.gatech.edu/", "field": "Physics", "opportunity_type": "Research", "year_level": ["Sophomore", "Junior"], "country": "USA", "state": "GA", "city": "Atlanta", "is_paid": True, "compensation": "$6,000–$7,000 + free housing", "deadline": "2026-02-15", "description": "10-week NSF REU at Georgia Tech. Open to all US undergrads. Condensed matter, quantum materials, astrophysics."},
    {"organization": "Brookhaven National Laboratory", "title": "Undergraduate Internship Programs", "url": "https://www.bnl.gov/education/college-students.php", "field": "Physics", "opportunity_type": "Internship", "year_level": ["Sophomore", "Junior", "Senior"], "country": "USA", "state": "NY", "city": "Upton", "is_paid": True, "compensation": "Stipend + housing", "deadline": "2026-01-07", "description": "Summer research at Brookhaven National Lab via DOE SULI. 350+ students per year. Open to all US citizens."},
    {"organization": "Oak Ridge National Laboratory", "title": "Research Student Internships (RSI)", "url": "https://education.ornl.gov/undergraduate/", "field": "General STEM", "opportunity_type": "Internship", "year_level": ["Sophomore", "Junior", "Senior"], "country": "USA", "state": "TN", "city": "Oak Ridge", "is_paid": True, "compensation": "Stipend + housing", "deadline": "2026-02-26", "description": "10–12 week summer research at ORNL. Open to all US citizens/permanent residents with 3.0+ GPA."},
    {"organization": "NOAA", "title": "Hollings Undergraduate Scholarship", "url": "https://www.noaa.gov/office-education/hollings-scholarship", "field": "Environmental Science", "opportunity_type": "Scholarship", "year_level": ["Sophomore"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$9,500/year for 2 years + paid summer internship", "deadline": "2026-01-31", "description": "Scholarship + 10-week paid summer internship at a NOAA facility. Open to all US undergrads in STEM with 3.0+ GPA."},

    # ── USA Fellowships (open to all eligible applicants) ────────────
    {"organization": "NSF", "title": "Graduate Research Fellowship Program (GRFP)", "url": "https://www.nsf.gov/funding/opportunities/grfp-nsf-graduate-research-fellowship-program/nsf25-547/solicitation", "field": "General STEM", "opportunity_type": "Fellowship", "year_level": ["Senior", "Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$37,000/year + $16,000 tuition for 3 years", "deadline": "2025-11-14", "description": "NSF's flagship fellowship for graduate students in STEM. 3 years of full funding. Open to US citizens/permanent residents."},
    {"organization": "Hertz Foundation", "title": "Hertz Fellowship", "url": "https://www.hertzfoundation.org/the-fellowship/apply-for-fellowship/", "field": "General STEM", "opportunity_type": "Fellowship", "year_level": ["Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$40,000+/year for 5 years + full tuition", "deadline": "2025-10-31", "description": "One of the most generous STEM fellowships. Full tuition + stipend for PhD in applied sciences. Open to all US citizens/permanent residents."},
    {"organization": "DOD", "title": "NDSEG Fellowship", "url": "https://ndseg.sysplus.com/", "field": "General STEM", "opportunity_type": "Fellowship", "year_level": ["Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "Full tuition + $38,400/year for 3 years", "deadline": "2025-11-01", "description": "Department of Defense fellowship for STEM PhD students. Open to US citizens and dual citizens."},
    {"organization": "DOE", "title": "SCGSR – Graduate Student Research", "url": "https://science.osti.gov/wdts/scgsr", "field": "General STEM", "opportunity_type": "Fellowship", "year_level": ["Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$3,600/month + travel", "deadline": "2026-05-06", "description": "PhD students conduct thesis research at a DOE national lab. 3–12 month projects. Open to US citizens/permanent residents."},
    {"organization": "GEM Consortium", "title": "GEM Fellowship", "url": "https://www.gemfellowship.org/gem-fellowship-program/", "field": "Engineering", "opportunity_type": "Fellowship", "year_level": ["Senior", "Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "Full tuition + stipend + paid internship", "deadline": "2025-11-07", "description": "MS and PhD fellowships in STEM for underrepresented groups. Includes paid summer internship. Open to US citizens/permanent residents."},
    {"organization": "DOD", "title": "SMART Scholarship-for-Service", "url": "https://www.smartscholarship.org/smart", "field": "General STEM", "opportunity_type": "Scholarship", "year_level": ["Junior", "Senior", "Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "Full tuition + $30,000–$46,000/year + internship", "deadline": "2025-12-01", "description": "Full scholarship for STEM students who commit to DoD service after graduation. Open to US, AU, CA, NZ, UK citizens."},
    {"organization": "Paul & Daisy Soros", "title": "Fellowships for New Americans", "url": "https://www.pdsoros.org/", "field": "General STEM", "opportunity_type": "Fellowship", "year_level": ["Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$90,000 over 2 years", "deadline": "2025-10-30", "description": "For immigrants and children of immigrants pursuing graduate study. 30 fellowships annually. Open to New Americans age 30 or younger."},
    {"organization": "HHMI", "title": "Gilliam Fellows Program", "url": "https://www.hhmi.org/programs/gilliam-fellows", "field": "Biology", "opportunity_type": "Fellowship", "year_level": ["Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "Up to $159,000 over 3 years + postdoc support", "deadline": "2026-10-01", "description": "For PhD students in biomedical sciences from underrepresented groups. Next competition opens Fall 2026. Open to all US institutions."},

    # ── USA Scholarships (open to all, some require nomination) ──────
    {"organization": "Goldwater Foundation", "title": "Goldwater Scholarship", "url": "https://goldwaterscholarship.gov/", "field": "General STEM", "opportunity_type": "Scholarship", "year_level": ["Sophomore", "Junior"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$7,500/year", "deadline": "2026-01-30", "description": "Premier undergraduate STEM scholarship. Requires institutional nomination. Open to sophomores and juniors at any US institution."},
    {"organization": "Udall Foundation", "title": "Udall Scholarship", "url": "https://www.udall.gov/", "field": "Environmental Science", "opportunity_type": "Scholarship", "year_level": ["Sophomore", "Junior"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "$7,000", "deadline": "2026-03-04", "description": "For students committed to environment, tribal policy, or Native healthcare. Requires faculty nomination."},
    {"organization": "SACNAS", "title": "NDiSTEM Conference Travel Scholarship", "url": "https://www.sacnas.org/conference", "field": "General STEM", "opportunity_type": "Conference", "year_level": ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"], "country": "USA", "state": None, "city": None, "is_paid": True, "compensation": "Travel grant", "deadline": "Rolling", "description": "Largest diversity in STEM conference. Research presentations, mentoring, and career expo. Open to all."},
    {"organization": "ACS", "title": "ACS National Meeting – Undergraduate Poster & Travel Grants", "url": "https://www.acs.org/meetings.html", "field": "Chemistry", "opportunity_type": "Conference", "year_level": ["Sophomore", "Junior", "Senior"], "country": "USA", "state": None, "city": None, "is_paid": False, "compensation": "Travel grants available", "deadline": "Rolling", "description": "Present research at the largest chemistry conference. Travel grants available for undergrads. Open to all."},

    # ── South Korea Programs (open to international students) ────────
    {"organization": "KAIST", "title": "KAI-X Summer Research Internship", "url": "https://kai-x.kaist.ac.kr/", "field": "General STEM", "opportunity_type": "Summer Program", "year_level": ["Junior", "Senior", "Graduate"], "country": "South Korea", "state": None, "city": "Daejeon", "is_paid": True, "compensation": "Round-trip airfare + dormitory (fully funded)", "deadline": "2026-02-15", "description": "7-week summer research at KAIST. Open to international undergrads (3rd/4th year) and Master's students in natural sciences."},
    {"organization": "KIST", "title": "KIST School Student Internship Program", "url": "https://www.kist.re.kr/kist_school_eng/StudentTrainingProgram.do", "field": "General STEM", "opportunity_type": "Internship", "year_level": ["Junior", "Senior", "Graduate"], "country": "South Korea", "state": None, "city": "Seoul", "is_paid": True, "compensation": "1.2–1.4M KRW/month + dormitory + insurance", "deadline": "2025-10-26", "description": "6-month research internship at KIST. AI, robotics, nanoscience, energy, biomedical. Open to international students."},
    {"organization": "Korean Government", "title": "GKS/KGSP – Global Korea Scholarship (Graduate)", "url": "https://www.studyinkorea.go.kr/", "field": "General STEM", "opportunity_type": "Scholarship", "year_level": ["Graduate"], "country": "South Korea", "state": None, "city": None, "is_paid": True, "compensation": "Full tuition + stipend + airfare", "deadline": "2026-02-25", "description": "Korean government scholarship for international graduate students. 2,000 slots across 71 countries."},
    {"organization": "POSTECH", "title": "POSTECH Summer Program (PSP)", "url": "https://international.postech.ac.kr/user/admission/psp/index.do", "field": "General STEM", "opportunity_type": "Summer Program", "year_level": ["Sophomore", "Junior", "Senior"], "country": "South Korea", "state": None, "city": "Pohang", "is_paid": True, "compensation": "Round-trip airfare provided", "deadline": "2026-02-15", "description": "6-week summer research at POSTECH. Open to international STEM undergrads and Master's students."},
    {"organization": "SNU", "title": "International Summer Program", "url": "https://summer.snu.ac.kr/en", "field": "General STEM", "opportunity_type": "Summer Program", "year_level": ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"], "country": "South Korea", "state": None, "city": "Seoul", "is_paid": False, "compensation": "20% early-bird tuition discount", "deadline": "2026-04-05", "description": "5-week intensive courses at Seoul National University. 71 courses in English. Open to all international students."},
    {"organization": "IBS", "title": "QNS Summer School Program", "url": "https://qns.science/2026-qns-summer-school/", "field": "Physics", "opportunity_type": "Summer Program", "year_level": ["Junior", "Senior", "Graduate"], "country": "South Korea", "state": None, "city": "Seoul", "is_paid": True, "compensation": "Airfare + accommodation provided", "deadline": "2026-05-01", "description": "4-week immersive quantum nanoscience research at IBS Center for Quantum Nanoscience. Open to international students."},
    {"organization": "Samsung Research", "title": "Global Research Internship", "url": "https://research.samsung.com/", "field": "Computer Science", "opportunity_type": "Internship", "year_level": ["Junior", "Senior", "Graduate"], "country": "South Korea", "state": None, "city": "Seoul", "is_paid": True, "compensation": "Competitive stipend", "deadline": "Rolling", "description": "Research internship at Samsung AI and advanced technology labs. Open to international students in CS and engineering."},

    # ── Competitions (open to all) ───────────────────────────────────
    {"organization": "iGEM Foundation", "title": "iGEM Competition", "url": "https://competition.igem.org/participation/rules-and-policies", "field": "Biology", "opportunity_type": "Competition", "year_level": ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"], "country": "USA", "state": None, "city": None, "is_paid": False, "compensation": None, "deadline": "Rolling", "description": "International synthetic biology competition. Teams design and build biological systems. Open to all universities worldwide."},
    {"organization": "COMAP", "title": "MCM/ICM – Mathematical Modeling Competition", "url": "https://www.contest.comap.com/undergraduate/contests/", "field": "Math", "opportunity_type": "Competition", "year_level": ["Freshman", "Sophomore", "Junior", "Senior"], "country": "USA", "state": None, "city": None, "is_paid": False, "compensation": None, "deadline": "2026-01-20", "description": "International mathematical modeling competition for undergraduate teams. 4-day challenge. Open to all universities worldwide."},
]


class OpportunityScraper:
    def __init__(self):
        load_dotenv()

        gemini_key = os.getenv("GEMINI_API_KEY")
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        for name, val in [
            ("GEMINI_API_KEY", gemini_key),
            ("FIRECRAWL_API_KEY", firecrawl_key),
            ("SUPABASE_URL", self.supabase_url),
            ("SUPABASE_SERVICE_ROLE_KEY", self.supabase_key),
        ]:
            if not val or val.startswith("여기에"):
                raise ValueError(f"{name} is not set in .env")

        self.genai = genai.Client(api_key=gemini_key)
        self.firecrawl = Firecrawl(api_key=firecrawl_key)

        self.usajobs_key = os.getenv("USAJOBS_API_KEY", "")
        self.usajobs_email = os.getenv("USAJOBS_EMAIL", "")
        self.adzuna_id = os.getenv("ADZUNA_APP_ID", "")
        self.adzuna_key = os.getenv("ADZUNA_APP_KEY", "")

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        self.stats = {
            "total": 0,
            "saved": 0,
            "errors": 0,
            "by_tier": {"curated": 0, "api": 0, "rotation": 0, "aggregator": 0},
        }
        self.today = date.today()
        self.weekday = self.today.weekday()  # 0=Mon … 6=Sun

    # ==================================================================
    # Utility helpers
    # ==================================================================

    def scrape_static(self, url: str, name: str) -> str | None:
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            logger.info(f"[{name}] Static scraped: {len(text)} chars")
            return text
        except Exception as e:
            logger.error(f"[{name}] Static failed: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_dynamic(self, url: str, name: str) -> str | None:
        try:
            result = self.firecrawl.scrape(url, formats=["markdown"])
            text = ""
            if isinstance(result, dict):
                text = result.get("markdown", "")
            if not text and hasattr(result, "markdown"):
                text = result.markdown or ""
            logger.info(f"[{name}] Dynamic scraped: {len(text)} chars")
            return text if text else None
        except Exception as e:
            logger.error(f"[{name}] Dynamic failed: {e}")
            self.stats["errors"] += 1
            return None

    def parse_with_gemini(self, raw_text: str, source: str, source_url: str) -> list[dict]:
        truncated = raw_text[:15000]
        prompt = f'''You are extracting STEM opportunities for college students in the USA or South Korea.
Return ONLY a valid JSON array. No markdown fences, no explanation.
If nothing found, return: []

STRICT RULES:
- ONLY include opportunities located in USA or South Korea.
- ONLY include opportunities for 2026 (deadlines in 2026 or Rolling).
- SKIP any opportunity whose deadline has already passed (before {self.today}).
- SKIP full-time permanent jobs — only student internships, research, fellowships, etc.

Each object:
{{
    "organization": "name",
    "title": "position title",
    "url": "apply link (use {source_url} if specific link not found)",
    "description": "2-3 sentences",
    "field": one of ["Chemistry","Biology","Physics","Computer Science","Engineering","Math","Data Science","Environmental Science","Neuroscience","Materials Science","Biomedical","Astronomy","General STEM"],
    "opportunity_type": one of ["Research","Internship","Fellowship","Scholarship","Competition","Conference","Summer Program","Co-op"],
    "year_level": array from ["Freshman","Sophomore","Junior","Senior","Graduate","Any"],
    "city": "city or null",
    "state": "US state abbrev or null",
    "country": "USA" or "South Korea",
    "is_remote": true or false,
    "deadline": "YYYY-MM-DD or Rolling or Unknown",
    "is_paid": true or false or null,
    "compensation": "details or null",
    "source": "{source}"
}}

"undergraduates"=["Freshman","Sophomore","Junior","Senior"]. Use "USA" for United States, "South Korea" for Korea.

TEXT:
{truncated}'''

        try:
            response = self.genai.models.generate_content(
                model="gemini-2.5-flash", contents=prompt,
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```json?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            opps = json.loads(text)
            if not isinstance(opps, list):
                opps = [opps]
            logger.info(f"[{source}] Gemini: {len(opps)} extracted")
            return opps
        except Exception as e:
            logger.error(f"[{source}] Gemini failed: {e}")
            self.stats["errors"] += 1
            return []

    def update_deadline_with_gemini(self, raw_text: str, program_name: str) -> str | None:
        truncated = raw_text[:8000]
        prompt = f'''Look at this webpage text for the program "{program_name}".
Find the application deadline for 2026.
Return ONLY the deadline in YYYY-MM-DD format, or "Rolling" if rolling admissions, or "Unknown" if not found.
No explanation, just the date string.

TEXT:
{truncated}'''
        try:
            response = self.genai.models.generate_content(
                model="gemini-2.5-flash", contents=prompt,
            )
            text = response.text.strip().strip('"').strip("'")
            if re.match(r"^\d{4}-\d{2}-\d{2}$", text) or text in ("Rolling", "Unknown"):
                return text
            return None
        except Exception:
            return None

    def save_to_supabase(self, opportunities: list[dict]) -> int:
        saved = 0
        api_url = f"{self.supabase_url}/rest/v1/opportunities"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        for opp in opportunities:
            if not opp.get("organization") or not opp.get("url"):
                continue
            payload = {
                "organization": opp.get("organization", ""),
                "title": opp.get("title", ""),
                "url": opp["url"],
                "description": (opp.get("description") or "")[:2000],
                "field": opp.get("field", "General STEM"),
                "opportunity_type": opp.get("opportunity_type", "Internship"),
                "year_level": opp.get("year_level", []),
                "city": opp.get("city"),
                "state": opp.get("state"),
                "country": opp.get("country", "USA"),
                "is_remote": opp.get("is_remote", False),
                "deadline": opp.get("deadline", "Unknown"),
                "start_date": opp.get("start_date"),
                "duration": opp.get("duration"),
                "is_paid": opp.get("is_paid"),
                "compensation": opp.get("compensation"),
                "source": opp.get("source", ""),
                "is_active": True,
            }
            try:
                resp = requests.post(api_url, headers=headers, json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    saved += 1
                else:
                    logger.warning(f"Supabase {resp.status_code}: {opp.get('title','?')} — {resp.text[:150]}")
            except Exception as e:
                logger.error(f"DB save fail [{opp.get('title','?')}]: {e}")
        self.stats["saved"] += saved
        logger.info(f"Saved {saved}/{len(opportunities)} to Supabase")
        return saved

    def save_to_json(self, opportunities: list[dict]):
        path = "opportunities.json"
        existing: list[dict] = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        urls = {o.get("url", "") for o in existing}
        new_count = 0
        for opp in opportunities:
            if opp.get("url") and opp["url"] not in urls:
                existing.append(opp)
                urls.add(opp["url"])
                new_count += 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, default=str, ensure_ascii=False)
        logger.info(f"JSON: {new_count} new, {len(existing)} total")

    def infer_field(self, keyword: str) -> str:
        kw = keyword.lower()
        mapping = {
            "chemistry": "Chemistry", "chemical": "Chemistry", "pharmaceutical": "Chemistry",
            "biology": "Biology", "biomedical": "Biomedical", "bio ": "Biology",
            "physics": "Physics", "quantum": "Physics",
            "computer": "Computer Science", "software": "Computer Science",
            "engineering": "Engineering", "mechanical": "Engineering", "electrical": "Engineering",
            "math": "Math", "statistic": "Math",
            "data": "Data Science", "machine learning": "Data Science",
            "environment": "Environmental Science", "climate": "Environmental Science",
            "neuro": "Neuroscience", "material": "Materials Science",
            "astro": "Astronomy", "space": "Astronomy",
        }
        for key, field in mapping.items():
            if key in kw:
                return field
        return "General STEM"

    # ==================================================================
    # TIER A — Curated Programs (always run, most reliable)
    # ==================================================================

    def tier_curated(self) -> list[dict]:
        all_opps: list[dict] = []
        batch_size = len(CURATED_PROGRAMS)

        for i, prog in enumerate(CURATED_PROGRAMS):
            opp = {
                "organization": prog["organization"],
                "title": prog["title"],
                "url": prog["url"],
                "description": prog.get("description", ""),
                "field": prog.get("field", "General STEM"),
                "opportunity_type": prog.get("opportunity_type", "Research"),
                "year_level": prog.get("year_level", ["Any"]),
                "city": prog.get("city"),
                "state": prog.get("state"),
                "country": prog.get("country", "USA"),
                "is_remote": prog.get("is_remote", False),
                "deadline": prog.get("deadline", "Unknown"),
                "is_paid": prog.get("is_paid"),
                "compensation": prog.get("compensation"),
                "source": "curated",
            }

            if opp["deadline"] == "Unknown":
                text = self.scrape_static(prog["url"], prog["organization"])
                if not text or len(text) < 200:
                    text = self.scrape_dynamic(prog["url"], prog["organization"])
                if text and len(text) > 200:
                    dl = self.update_deadline_with_gemini(text, prog["title"])
                    if dl:
                        opp["deadline"] = dl
                        logger.info(f"  [{prog['organization']}] deadline → {dl}")
                time.sleep(0.5)

            all_opps.append(opp)
            if (i + 1) % 10 == 0:
                logger.info(f"  Curated: {i + 1}/{batch_size} processed")

        self.stats["by_tier"]["curated"] += len(all_opps)
        return all_opps

    # ==================================================================
    # TIER B — APIs (daily)
    # ==================================================================

    def tier_usajobs(self) -> list[dict]:
        if not self.usajobs_key or self.usajobs_key.startswith("여기에"):
            logger.warning("[USAJobs] API key not set, skipping")
            return []

        queries = [
            "chemistry internship", "biology research",
            "computer science intern", "engineering intern",
            "STEM internship", "physics intern",
        ]
        api_headers = {
            "Authorization-Key": self.usajobs_key,
            "User-Agent": self.usajobs_email,
            "Host": "data.usajobs.gov",
        }
        all_opps: list[dict] = []

        for query in queries:
            try:
                params = {"Keyword": query, "HiringPath": "students", "ResultsPerPage": 50}
                resp = requests.get(
                    "https://data.usajobs.gov/api/Search",
                    headers=api_headers, params=params, timeout=15,
                )
                resp.raise_for_status()
                items = resp.json().get("SearchResult", {}).get("SearchResultItems", [])

                for item in items:
                    obj = item.get("MatchedObjectDescriptor", {})
                    locations = obj.get("PositionLocation", [{}])
                    loc = locations[0] if locations else {}
                    loc_name = loc.get("LocationName", "")
                    city, state = None, None
                    if ", " in loc_name:
                        parts = loc_name.split(", ")
                        city, state = parts[0], (parts[1] if len(parts) > 1 else None)

                    remuneration = obj.get("PositionRemuneration", [{}])
                    pay = remuneration[0] if remuneration else {}
                    min_p, max_p = pay.get("MinimumRange", ""), pay.get("MaximumRange", "")
                    comp = f"${min_p}-${max_p}" if min_p else None

                    all_opps.append({
                        "organization": obj.get("OrganizationName", ""),
                        "title": obj.get("PositionTitle", ""),
                        "url": obj.get("PositionURI", ""),
                        "description": (obj.get("QualificationSummary", "") or "")[:500],
                        "field": self.infer_field(query),
                        "opportunity_type": "Internship",
                        "year_level": ["Any"],
                        "city": city, "state": state, "country": "USA",
                        "is_remote": False,
                        "deadline": obj.get("ApplicationCloseDate", "Unknown"),
                        "is_paid": bool(comp), "compensation": comp,
                        "source": "USAJobs",
                    })

                logger.info(f"[USAJobs] '{query}': {len(items)} results")
                time.sleep(1)
            except Exception as e:
                logger.error(f"[USAJobs] '{query}' failed: {e}")
                self.stats["errors"] += 1

        self.stats["by_tier"]["api"] += len(all_opps)
        return all_opps

    def tier_adzuna(self) -> list[dict]:
        if not self.adzuna_id or self.adzuna_id.startswith("여기에"):
            logger.warning("[Adzuna] API keys not set, skipping")
            return []

        searches = [
            ("us", "chemistry research internship"),
            ("us", "biology lab internship"),
            ("us", "computer science internship"),
            ("us", "engineering internship"),
            ("us", "data science internship"),
            ("us", "STEM research internship"),
        ]
        all_opps: list[dict] = []

        for cc, query in searches:
            try:
                params = {
                    "app_id": self.adzuna_id, "app_key": self.adzuna_key,
                    "results_per_page": 25, "what": query,
                    "what_exclude": "senior manager director lead principal",
                    "max_days_old": 7, "sort_by": "date",
                    "content-type": "application/json",
                }
                resp = requests.get(
                    f"https://api.adzuna.com/v1/api/jobs/{cc}/search/1",
                    params=params, timeout=15,
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])

                for r in results:
                    title = r.get("title", "")
                    desc = re.sub(r"<[^>]+>", "", r.get("description", "")).strip()[:500]
                    combined = (title + " " + desc).lower()
                    if any(w in combined for w in ["senior", "manager", "director", "10+ years", "lead architect"]):
                        continue

                    loc_name = r.get("location", {}).get("display_name", "")
                    city = loc_name.split(",")[0] if loc_name else None

                    sal_min, sal_max = r.get("salary_min"), r.get("salary_max")
                    comp = None
                    if sal_min and sal_max:
                        comp = f"${int(sal_min):,}-${int(sal_max):,}/year"
                    elif sal_min:
                        comp = f"${int(sal_min):,}/year"

                    all_opps.append({
                        "organization": r.get("company", {}).get("display_name", "Unknown"),
                        "title": title, "url": r.get("redirect_url", ""),
                        "description": desc,
                        "field": self.infer_field(query),
                        "opportunity_type": "Internship",
                        "year_level": ["Any"],
                        "city": city, "state": None, "country": "USA",
                        "is_remote": "remote" in combined,
                        "deadline": "Unknown",
                        "is_paid": bool(comp), "compensation": comp,
                        "source": "Adzuna",
                    })

                logger.info(f"[Adzuna] {cc}/{query}: {len(results)} results")
                time.sleep(1)
            except Exception as e:
                logger.error(f"[Adzuna] {cc}/{query} failed: {e}")
                self.stats["errors"] += 1

        self.stats["by_tier"]["api"] += len(all_opps)
        return all_opps

    # ==================================================================
    # TIER C — Aggregator scraping (rotate by weekday)
    # ==================================================================

    def tier_aggregators(self) -> list[dict]:
        schedule: dict[int, list[tuple[str, str, str]]] = {
            0: [("Pathways to Science", "https://pathwaystoscience.org/undergrads.aspx", "dynamic")],
            1: [("NSF REU Search", "https://www.nsf.gov/funding/initiatives/reu/search", "dynamic")],
            2: [("Cientifico Latino REU", "https://www.cientificolatino.com/reu", "dynamic")],
            3: [("Pathways to Science – Advanced", "https://pathwaystoscience.org/programs.aspx?adv=adv&descriptorhub=SummerResearch_Summer+Research+Opportunity", "dynamic")],
            4: [("NSF REU Search", "https://www.nsf.gov/funding/initiatives/reu/search", "dynamic")],
            5: [],
            6: [],
        }

        sites = schedule.get(self.weekday, [])
        if not sites:
            logger.info("[Aggregators] No aggregator scraping today")
            return []

        all_opps: list[dict] = []
        for name, url, method in sites:
            logger.info(f"[Aggregators] Scraping: {name}")
            if method == "dynamic":
                text = self.scrape_dynamic(url, name)
            else:
                text = self.scrape_static(url, name)

            if text:
                opps = self.parse_with_gemini(text, name, url)
                all_opps.extend(opps)
            time.sleep(3)

        self.stats["by_tier"]["aggregator"] += len(all_opps)
        return all_opps

    # ==================================================================
    # TIER D — Indeed rotation (reduced to 1 query/day)
    # ==================================================================

    def tier_indeed(self) -> list[dict]:
        queries_by_day: dict[int, str] = {
            0: "chemistry research internship 2026",
            1: "biology research assistant summer 2026",
            2: "physics research internship summer 2026",
            3: "materials science intern 2026",
            4: "environmental science internship 2026",
        }

        query = queries_by_day.get(self.weekday)
        if not query:
            logger.info("[Indeed] No search today (weekend)")
            return []

        url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&sort=date"
        logger.info(f"[Indeed] Searching: '{query}'")
        text = self.scrape_dynamic(url, f"Indeed:{query[:30]}")
        if not text:
            return []

        opps = self.parse_with_gemini(text, "Indeed", url)
        self.stats["by_tier"]["rotation"] += len(opps)
        return opps

    # ==================================================================
    # Main runner
    # ==================================================================

    def run(self) -> list[dict]:
        start = time.time()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        logger.info("=" * 60)
        logger.info(f"OpportunityHub Scraper v3 — {days[self.weekday]} {self.today}")
        logger.info("=" * 60)

        all_opps: list[dict] = []

        tiers = [
            ("Tier A: Curated Programs", self.tier_curated),
            ("Tier B: USAJobs API", self.tier_usajobs),
            ("Tier B: Adzuna API", self.tier_adzuna),
            ("Tier C: Aggregator Scraping", self.tier_aggregators),
            ("Tier D: Indeed Search", self.tier_indeed),
        ]

        for name, func in tiers:
            try:
                logger.info(f"\n{'─' * 40}")
                logger.info(f"▶ {name}")
                opps = func()
                all_opps.extend(opps)
                logger.info(f"  → {len(opps)} opportunities")
            except Exception as e:
                logger.error(f"  ✗ {name} CRASHED: {e}")
                self.stats["errors"] += 1

        seen: set[str] = set()
        unique: list[dict] = []
        for opp in all_opps:
            u = opp.get("url", "")
            if u and u not in seen:
                seen.add(u)
                unique.append(opp)

        allowed_countries = {"USA", "United States", "South Korea", "Korea"}
        filtered: list[dict] = []
        for opp in unique:
            country = opp.get("country", "")
            if country and country not in allowed_countries:
                continue
            deadline = opp.get("deadline", "Unknown")
            if deadline not in ("Unknown", "Rolling", "", None):
                try:
                    dl = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
                    if dl < self.today:
                        continue
                except (ValueError, TypeError):
                    pass
            filtered.append(opp)

        dropped = len(unique) - len(filtered)
        if dropped:
            logger.info(f"Filtered out {dropped} (expired or non-USA/Korea)")
        unique = filtered

        self.stats["total"] = len(unique)

        if unique:
            self.save_to_supabase(unique)
            self.save_to_json(unique)

        elapsed = time.time() - start
        logger.info(f"\n{'=' * 60}")
        logger.info(f"COMPLETE in {elapsed:.1f}s")
        logger.info(
            f"  Total: {self.stats['total']} | "
            f"Saved: {self.stats['saved']} | "
            f"Errors: {self.stats['errors']}"
        )
        logger.info(
            f"  By tier: Curated={self.stats['by_tier']['curated']}, "
            f"API={self.stats['by_tier']['api']}, "
            f"Aggregator={self.stats['by_tier']['aggregator']}, "
            f"Indeed={self.stats['by_tier']['rotation']}"
        )
        logger.info("=" * 60)

        return unique


if __name__ == "__main__":
    scraper = OpportunityScraper()
    scraper.run()
