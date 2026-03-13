import os
import json
import time
import re
import logging
from datetime import datetime, date
from urllib.parse import urlparse
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from firecrawl import Firecrawl
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel, field_validator, model_validator

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
# Validation & Normalization
# ---------------------------------------------------------------------------
VALID_FIELDS = {
    "Chemistry", "Biology", "Physics", "Computer Science", "Engineering",
    "Math", "Data Science", "Environmental Science", "Neuroscience",
    "Materials Science", "Biomedical", "Astronomy", "General STEM",
}
VALID_TYPES = {
    "Research", "Internship", "Fellowship", "Scholarship",
    "Competition", "Conference", "Summer Program", "Co-op",
}
VALID_COUNTRIES = {"USA", "South Korea"}
VALID_YEARS = {"Freshman", "Sophomore", "Junior", "Senior", "Graduate", "Any"}

COUNTRY_ALIASES: dict[str, str] = {
    "united states": "USA", "us": "USA", "u.s.": "USA", "u.s.a.": "USA",
    "america": "USA", "usa": "USA",
    "korea": "South Korea", "south korea": "South Korea",
    "republic of korea": "South Korea", "rok": "South Korea",
}

FIELD_ALIASES: dict[str, str] = {
    "cs": "Computer Science", "computing": "Computer Science",
    "computer engineering": "Computer Science", "software": "Computer Science",
    "bio": "Biology", "biological": "Biology", "life sciences": "Biology",
    "chem": "Chemistry", "chemical": "Chemistry",
    "phys": "Physics", "applied physics": "Physics",
    "ee": "Engineering", "mechanical engineering": "Engineering",
    "electrical engineering": "Engineering", "civil engineering": "Engineering",
    "mathematics": "Math", "applied math": "Math", "statistics": "Math",
    "ml": "Data Science", "machine learning": "Data Science", "ai": "Data Science",
    "environmental": "Environmental Science", "ecology": "Environmental Science",
    "climate": "Environmental Science", "earth science": "Environmental Science",
    "neuro": "Neuroscience", "cognitive science": "Neuroscience",
    "materials": "Materials Science", "material science": "Materials Science",
    "bme": "Biomedical", "bioengineering": "Biomedical",
    "astro": "Astronomy", "astrophysics": "Astronomy", "space science": "Astronomy",
    "stem": "General STEM", "multidisciplinary": "General STEM",
}

TYPE_ALIASES: dict[str, str] = {
    "reu": "Research", "research experience": "Research",
    "lab position": "Research", "research assistant": "Research",
    "intern": "Internship", "co-op": "Co-op", "coop": "Co-op",
    "grant": "Fellowship", "traineeship": "Fellowship",
    "award": "Scholarship", "prize": "Scholarship",
    "hackathon": "Competition", "challenge": "Competition",
    "workshop": "Conference", "symposium": "Conference",
    "summer school": "Summer Program", "summer research": "Summer Program",
}


def normalize_country(val: str | None) -> str:
    if not val:
        return "USA"
    return COUNTRY_ALIASES.get(val.strip().lower(), val.strip())


def normalize_field(val: str | None) -> str:
    if not val:
        return "General STEM"
    v = val.strip()
    if v in VALID_FIELDS:
        return v
    return FIELD_ALIASES.get(v.lower(), v)


def normalize_type(val: str | None) -> str:
    if not val:
        return "Internship"
    v = val.strip()
    if v in VALID_TYPES:
        return v
    return TYPE_ALIASES.get(v.lower(), v)


def parse_deadline(dl: str) -> date | None:
    """Parse a deadline string to a date, returning None for non-date values."""
    if not dl or dl in ("Unknown", "Rolling", ""):
        return None
    try:
        return datetime.strptime(dl[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def is_valid_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


class OpportunityModel(BaseModel):
    organization: str
    title: str
    url: str
    description: str = ""
    field: str = "General STEM"
    opportunity_type: str = "Internship"
    year_level: list[str] = ["Any"]
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"
    is_remote: bool = False
    deadline: str = "Unknown"
    is_paid: Optional[bool] = None
    compensation: Optional[str] = None
    source: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_all(cls, values: dict) -> dict:
        if isinstance(values, dict):
            values["country"] = normalize_country(values.get("country"))
            values["field"] = normalize_field(values.get("field"))
            values["opportunity_type"] = normalize_type(values.get("opportunity_type"))
            yl = values.get("year_level", ["Any"])
            if isinstance(yl, str):
                yl = [yl]
            values["year_level"] = [y for y in yl if y in VALID_YEARS] or ["Any"]
        return values

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not is_valid_url(v):
            raise ValueError(f"Invalid URL: {v}")
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if v not in VALID_COUNTRIES:
            raise ValueError(f"Invalid country: {v}")
        return v

    @field_validator("field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        if v not in VALID_FIELDS:
            raise ValueError(f"Invalid field: {v}")
        return v

    @field_validator("opportunity_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_TYPES:
            raise ValueError(f"Invalid type: {v}")
        return v


def validate_opportunity(opp: dict) -> dict | None:
    """Validate and normalize an opportunity dict. Returns None if invalid."""
    try:
        model = OpportunityModel(**opp)
        return model.model_dump()
    except Exception as e:
        logger.debug(f"Validation dropped: {opp.get('title', '?')} — {e}")
        return None


def _load_curated_programs() -> list[dict]:
    """Load curated programs from external JSON file."""
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curated_programs.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            programs = json.load(f)
        logger.info(f"Loaded {len(programs)} curated programs from {json_path}")
        return programs
    except FileNotFoundError:
        logger.warning(f"curated_programs.json not found at {json_path}, using empty list")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse curated_programs.json: {e}")
        return []


CURATED_PROGRAMS: list[dict] = _load_curated_programs()


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

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
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
            resp = self.session.get(url, timeout=15)
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), retry=retry_if_exception_type(Exception), reraise=True)
    def _call_gemini(self, prompt: str, json_mode: bool = False) -> str:
        config = {}
        if json_mode:
            config = {"response_mime_type": "application/json"}
        response = self.genai.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config if config else None,
        )
        return response.text.strip()

    def _clean_json_response(self, text: str) -> str:
        """Strip markdown fences and other non-JSON artifacts from Gemini output."""
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?\s*```\s*$", "", text)
        bracket = text.find("[")
        if bracket > 0 and bracket < 20:
            text = text[bracket:]
        return text.strip()

    def parse_with_gemini(self, raw_text: str, source: str, source_url: str) -> list[dict]:
        truncated = raw_text[:15000]
        prompt = f'''Extract STEM opportunities for US/South Korea college students from the text below.
Return a JSON array of objects. If nothing found, return [].

RULES:
- ONLY USA or South Korea locations.
- Deadlines in 2026 or later, or Rolling. Skip anything before {self.today}.
- Skip full-time permanent jobs. Only student programs: internships, REUs, fellowships, scholarships, etc.

Schema per object:
{{
  "organization": "string",
  "title": "string",
  "url": "string (use {source_url} as fallback)",
  "description": "string (2-3 sentences)",
  "field": "Chemistry|Biology|Physics|Computer Science|Engineering|Math|Data Science|Environmental Science|Neuroscience|Materials Science|Biomedical|Astronomy|General STEM",
  "opportunity_type": "Research|Internship|Fellowship|Scholarship|Competition|Conference|Summer Program|Co-op",
  "year_level": ["Freshman","Sophomore","Junior","Senior","Graduate","Any"],
  "city": "string|null",
  "state": "string|null (US state abbrev)",
  "country": "USA|South Korea",
  "is_remote": "boolean",
  "deadline": "YYYY-MM-DD|Rolling|Unknown",
  "is_paid": "boolean|null",
  "compensation": "string|null",
  "source": "{source}"
}}

Use "USA" for United States, "South Korea" for Korea. "undergraduates" = Freshman through Senior.

TEXT:
{truncated}'''

        try:
            text = self._call_gemini(prompt, json_mode=True)
            text = self._clean_json_response(text)
            opps = json.loads(text)
            if not isinstance(opps, list):
                opps = [opps]
            logger.info(f"[{source}] Gemini: {len(opps)} extracted")
            return opps
        except json.JSONDecodeError as e:
            logger.error(f"[{source}] Gemini JSON parse error: {e}")
            self.stats["errors"] += 1
            return []
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
            text = self._call_gemini(prompt)
            text = text.strip('"').strip("'")
            if re.match(r"^\d{4}-\d{2}-\d{2}$", text) or text in ("Rolling", "Unknown"):
                return text
            return None
        except Exception as e:
            logger.warning(f"[{program_name}] Deadline extraction failed: {e}")
            return None

    def save_to_supabase(self, opportunities: list[dict]) -> int:
        saved = 0
        dupes = 0
        invalid = 0
        api_url = f"{self.supabase_url}/rest/v1/opportunities?on_conflict=url"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        for opp in opportunities:
            validated = validate_opportunity(opp)
            if not validated:
                invalid += 1
                continue
            payload = {
                "organization": validated["organization"],
                "title": validated["title"],
                "url": validated["url"],
                "description": (validated.get("description") or "")[:2000],
                "field": validated["field"],
                "opportunity_type": validated["opportunity_type"],
                "year_level": validated["year_level"],
                "city": validated.get("city"),
                "state": validated.get("state"),
                "country": validated["country"],
                "is_remote": validated.get("is_remote", False),
                "deadline": validated.get("deadline", "Unknown"),
                "start_date": opp.get("start_date"),
                "duration": opp.get("duration"),
                "is_paid": validated.get("is_paid"),
                "compensation": validated.get("compensation"),
                "source": validated.get("source", ""),
                "is_active": True,
            }
            try:
                resp = self.session.post(api_url, headers=headers, json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    saved += 1
                elif resp.status_code == 409:
                    dupes += 1
                else:
                    logger.warning(f"Supabase {resp.status_code}: {validated.get('title','?')}")
            except Exception as e:
                logger.error(f"DB save fail [{validated.get('title','?')}]: {e}")
        self.stats["saved"] += saved
        if invalid:
            logger.info(f"Validation dropped {invalid} invalid opportunities")
        logger.info(f"Saved {saved}/{len(opportunities)} to Supabase ({dupes} existing, updated)")
        return saved

    def save_to_json(self, opportunities: list[dict]):
        path = "opportunities.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(opportunities, f, indent=2, default=str, ensure_ascii=False)
        logger.info(f"JSON backup: {len(opportunities)} opportunities written")

    def infer_field(self, keyword: str) -> str:
        kw = keyword.lower()
        for alias, field in FIELD_ALIASES.items():
            if alias in kw:
                return field
        return "General STEM"

    # ==================================================================
    # TIER A — Curated Programs (always run, most reliable)
    # ==================================================================

    def tier_curated(self) -> list[dict]:
        all_opps: list[dict] = []
        total = len(CURATED_PROGRAMS)

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
                time.sleep(1)

            all_opps.append(opp)
            if (i + 1) % 10 == 0:
                logger.info(f"  Curated: {i + 1}/{total} processed")

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
            "math intern", "environmental science intern",
            "biomedical intern", "materials science intern",
            "neuroscience intern", "data science intern",
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
                resp = self.session.get(
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
                time.sleep(2)
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
            ("us", "physics research internship"),
            ("us", "math internship"),
            ("us", "environmental science internship"),
            ("us", "biomedical research internship"),
            ("us", "materials science internship"),
            ("us", "neuroscience research internship"),
            ("us", "astronomy astrophysics internship"),
            ("us", "undergraduate research fellowship"),
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
                resp = self.session.get(
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
                time.sleep(2)
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
            0: [
                ("Pathways to Science", "https://pathwaystoscience.org/undergrads.aspx", "dynamic"),
                ("ACS Get Experience", "https://www.acs.org/get-experience.html", "static"),
            ],
            1: [
                ("NSF REU Search", "https://www.nsf.gov/funding/initiatives/reu/search", "dynamic"),
                ("ORISE Zintellect", "https://www.zintellect.com/Catalog", "dynamic"),
            ],
            2: [
                ("Cientifico Latino REU", "https://www.cientificolatino.com/reu", "dynamic"),
                ("ACS Student Internships", "https://www.acs.org/education/students/college/experienceopp.html", "static"),
            ],
            3: [
                ("Pathways to Science – Advanced", "https://pathwaystoscience.org/programs.aspx?adv=adv&descriptorhub=SummerResearch_Summer+Research+Opportunity", "dynamic"),
                ("ORISE STEM", "https://orise.orau.gov/doe-omni/", "static"),
            ],
            4: [
                ("NSF REU Search", "https://www.nsf.gov/funding/initiatives/reu/search", "dynamic"),
                ("ACS Careers", "https://www.acs.org/careers.html", "static"),
            ],
            5: [
                ("Pathways to Science – Fellowships", "https://pathwaystoscience.org/programs.aspx?adv=adv&descriptorhub=GradFellowships_Graduate+Fellowships", "dynamic"),
            ],
            6: [
                ("Cientifico Latino REU", "https://www.cientificolatino.com/reu", "dynamic"),
            ],
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
                if not text or len(text) < 200:
                    text = self.scrape_dynamic(url, name)

            if text:
                opps = self.parse_with_gemini(text, name, url)
                all_opps.extend(opps)
            time.sleep(2)

        self.stats["by_tier"]["aggregator"] += len(all_opps)
        return all_opps

    # ==================================================================
    # TIER D — Indeed rotation (reduced to 1 query/day)
    # ==================================================================

    def tier_indeed(self) -> list[dict]:
        queries_by_day: dict[int, list[str]] = {
            0: ["chemistry research internship 2026", "biomedical research intern 2026"],
            1: ["biology research assistant summer 2026", "neuroscience research intern 2026"],
            2: ["physics research internship summer 2026", "astronomy astrophysics intern 2026"],
            3: ["materials science intern 2026", "data science research intern 2026"],
            4: ["environmental science internship 2026", "math statistics intern 2026"],
            5: ["computer science research intern 2026"],
            6: ["engineering research internship summer 2026"],
        }

        day_queries = queries_by_day.get(self.weekday, [])
        if not day_queries:
            logger.info("[Indeed] No search today")
            return []

        all_opps: list[dict] = []
        for query in day_queries:
            url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&sort=date"
            logger.info(f"[Indeed] Searching: '{query}'")
            text = self.scrape_dynamic(url, f"Indeed:{query[:30]}")
            if text:
                opps = self.parse_with_gemini(text, "Indeed", url)
                all_opps.extend(opps)
            time.sleep(2)

        self.stats["by_tier"]["rotation"] += len(all_opps)
        return all_opps

    # ==================================================================
    # Cleanup — delete expired opportunities from Supabase
    # ==================================================================

    def cleanup_expired(self):
        api_url = f"{self.supabase_url}/rest/v1/opportunities"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }

        try:
            resp = self.session.get(
                f"{api_url}?select=id,deadline&deadline=not.is.null&deadline=neq.Unknown&deadline=neq.Rolling",
                headers=headers, timeout=15,
            )
            rows = resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logger.error(f"[Cleanup] Failed to fetch deadlines: {e}")
            return

        expired_ids = []
        for row in rows:
            d = parse_deadline(row.get("deadline", ""))
            if d and d < self.today:
                expired_ids.append(row["id"])

        if not expired_ids:
            logger.info("[Cleanup] No expired opportunities to delete")
            return

        deleted = 0
        batch_size = 50
        for i in range(0, len(expired_ids), batch_size):
            batch = expired_ids[i:i + batch_size]
            id_csv = ",".join(str(oid) for oid in batch)
            try:
                resp = self.session.delete(
                    f"{api_url}?id=in.({id_csv})", headers=headers, timeout=15,
                )
                if resp.status_code in (200, 204):
                    deleted += len(batch)
            except Exception as e:
                logger.warning(f"[Cleanup] Batch delete failed: {e}")

        logger.info(f"[Cleanup] Deleted {deleted}/{len(expired_ids)} expired opportunities")

    # ==================================================================
    # Main runner
    # ==================================================================

    def run(self) -> list[dict]:
        start = time.time()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        logger.info("=" * 60)
        logger.info(f"OpportunityHub Scraper v5 — {days[self.weekday]} {self.today}")
        logger.info("=" * 60)

        logger.info("\n▶ Step 0: Cleaning up expired opportunities")
        self.cleanup_expired()

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

        allowed_countries = VALID_COUNTRIES | set(COUNTRY_ALIASES)
        filtered: list[dict] = []
        for opp in unique:
            country = opp.get("country", "")
            if country and country not in allowed_countries:
                continue
            dl_date = parse_deadline(opp.get("deadline", "Unknown"))
            if dl_date and dl_date < self.today:
                continue
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

        self._health_check()
        self._write_gh_summary(elapsed)

        return unique

    def _health_check(self):
        try:
            resp = self.session.head(
                f"{self.supabase_url}/rest/v1/opportunities?is_active=eq.true",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Prefer": "count=exact",
                },
                timeout=10,
            )
            count_header = resp.headers.get("content-range", "")
            if "/" in count_header:
                count = int(count_header.split("/")[1])
                logger.info(f"[Health] DB has {count} active opportunities")
                if count == 0:
                    logger.warning("[Health] WARNING: Database has 0 active opportunities!")
            else:
                logger.warning(f"[Health] Could not parse count from response")
        except Exception as e:
            logger.warning(f"[Health] Check failed: {e}")

    def _write_gh_summary(self, elapsed: float):
        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if not summary_path:
            return
        try:
            tiers = self.stats["by_tier"]
            md = f"""## OpportunityHub Scraper Report

| Metric | Value |
|--------|-------|
| Date | {self.today} |
| Runtime | {elapsed:.1f}s |
| Total found | {self.stats['total']} |
| Saved to DB | {self.stats['saved']} |
| Errors | {self.stats['errors']} |

### By Tier
| Tier | Count |
|------|-------|
| Curated Programs | {tiers['curated']} |
| APIs (USAJobs + Adzuna) | {tiers['api']} |
| Aggregators | {tiers['aggregator']} |
| Indeed | {tiers['rotation']} |
"""
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(md)
            logger.info("[Summary] Wrote GitHub Actions step summary")
        except Exception as e:
            logger.debug(f"[Summary] Could not write: {e}")


if __name__ == "__main__":
    scraper = OpportunityScraper()
    scraper.run()
