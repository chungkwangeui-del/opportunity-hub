import os
import json
import time
import re
import logging
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
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

        genai.configure(api_key=gemini_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
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
            "by_tier": {"api": 0, "rotation": 0, "programs": 0},
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
        prompt = f'''You are extracting STEM opportunities for US college students.
Return ONLY a valid JSON array. No markdown fences, no explanation.
If nothing found, return: []

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
    "country": "country in English",
    "is_remote": true or false,
    "deadline": "YYYY-MM-DD or Rolling or Unknown",
    "is_paid": true or false or null,
    "compensation": "details or null",
    "source": "{source}"
}}

Only student opportunities. "undergraduates"=["Freshman","Sophomore","Junior","Senior"]. USA for United States.

TEXT:
{truncated}'''

        try:
            response = self.model.generate_content(prompt)
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
            "chemistry": "Chemistry",
            "chemical": "Chemistry",
            "pharmaceutical": "Chemistry",
            "biology": "Biology",
            "biomedical": "Biomedical",
            "bio ": "Biology",
            "physics": "Physics",
            "quantum": "Physics",
            "computer": "Computer Science",
            "software": "Computer Science",
            "engineering": "Engineering",
            "mechanical": "Engineering",
            "electrical": "Engineering",
            "math": "Math",
            "statistic": "Math",
            "data": "Data Science",
            "machine learning": "Data Science",
            "environment": "Environmental Science",
            "climate": "Environmental Science",
            "neuro": "Neuroscience",
            "material": "Materials Science",
            "astro": "Astronomy",
            "space": "Astronomy",
        }
        for key, field in mapping.items():
            if key in kw:
                return field
        return "General STEM"

    # ==================================================================
    # TIER 1 — APIs (daily, always fresh data, no blocking)
    # ==================================================================

    def tier1_usajobs(self) -> list[dict]:
        if not self.usajobs_key or self.usajobs_key.startswith("여기에"):
            logger.warning("[USAJobs] API key not set, skipping")
            return []

        queries = [
            "chemistry internship",
            "biology research",
            "computer science intern",
            "engineering intern",
            "STEM internship",
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
                    headers=api_headers,
                    params=params,
                    timeout=15,
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

                    all_opps.append(
                        {
                            "organization": obj.get("OrganizationName", ""),
                            "title": obj.get("PositionTitle", ""),
                            "url": obj.get("PositionURI", ""),
                            "description": (obj.get("QualificationSummary", "") or "")[:500],
                            "field": self.infer_field(query),
                            "opportunity_type": "Internship",
                            "year_level": ["Any"],
                            "city": city,
                            "state": state,
                            "country": "USA",
                            "is_remote": False,
                            "deadline": obj.get("ApplicationCloseDate", "Unknown"),
                            "is_paid": bool(comp),
                            "compensation": comp,
                            "source": "USAJobs",
                        }
                    )

                logger.info(f"[USAJobs] '{query}': {len(items)} results")
                time.sleep(1)
            except Exception as e:
                logger.error(f"[USAJobs] '{query}' failed: {e}")
                self.stats["errors"] += 1

        self.stats["by_tier"]["api"] += len(all_opps)
        return all_opps

    def tier1_adzuna(self) -> list[dict]:
        if not self.adzuna_id or self.adzuna_id.startswith("여기에"):
            logger.warning("[Adzuna] API keys not set, skipping")
            return []

        searches = [
            ("us", "chemistry research internship"),
            ("us", "biology lab internship"),
            ("us", "computer science internship"),
            ("us", "engineering internship"),
            ("us", "data science internship"),
            ("gb", "STEM internship"),
            ("de", "science internship"),
        ]
        country_map = {"us": "USA", "gb": "UK", "de": "Germany"}
        all_opps: list[dict] = []

        for cc, query in searches:
            try:
                params = {
                    "app_id": self.adzuna_id,
                    "app_key": self.adzuna_key,
                    "results_per_page": 50,
                    "what": query,
                    "max_days_old": 7,
                    "sort_by": "date",
                    "content-type": "application/json",
                }
                resp = requests.get(
                    f"https://api.adzuna.com/v1/api/jobs/{cc}/search/1",
                    params=params,
                    timeout=15,
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])

                for r in results:
                    desc = re.sub(r"<[^>]+>", "", r.get("description", "")).strip()[:500]
                    loc_name = r.get("location", {}).get("display_name", "")
                    city = loc_name.split(",")[0] if loc_name else None

                    sal_min, sal_max = r.get("salary_min"), r.get("salary_max")
                    comp = None
                    if sal_min and sal_max:
                        comp = f"${int(sal_min):,}-${int(sal_max):,}/year"
                    elif sal_min:
                        comp = f"${int(sal_min):,}/year"

                    all_opps.append(
                        {
                            "organization": r.get("company", {}).get("display_name", "Unknown"),
                            "title": r.get("title", ""),
                            "url": r.get("redirect_url", ""),
                            "description": desc,
                            "field": self.infer_field(query),
                            "opportunity_type": "Internship",
                            "year_level": ["Any"],
                            "city": city,
                            "state": None,
                            "country": country_map.get(cc, cc.upper()),
                            "is_remote": "remote" in (r.get("title", "") + desc).lower(),
                            "deadline": "Unknown",
                            "is_paid": bool(comp),
                            "compensation": comp,
                            "source": "Adzuna",
                        }
                    )

                logger.info(f"[Adzuna] {cc}/{query}: {len(results)} results")
                time.sleep(1)
            except Exception as e:
                logger.error(f"[Adzuna] {cc}/{query} failed: {e}")
                self.stats["errors"] += 1

        self.stats["by_tier"]["api"] += len(all_opps)
        return all_opps

    # ==================================================================
    # TIER 2 — Search rotation (daily, different queries per weekday)
    # ==================================================================

    def tier2_rotation(self) -> list[dict]:
        schedule: dict[int, list[str]] = {
            0: ["chemistry research assistant 2026", "pharmaceutical internship summer"],
            1: ["biology lab technician internship", "biomedical research intern 2026"],
            2: ["computer science internship summer 2026", "software engineering intern research lab"],
            3: ["physics research internship summer", "materials science intern 2026"],
            4: ["data science internship summer 2026", "machine learning research intern"],
            5: ["environmental science internship", "neuroscience research assistant summer"],
            6: [],  # Sunday → Tier 3 instead
        }

        queries = schedule.get(self.weekday, [])
        if not queries:
            logger.info("[Tier2] No rotation today (Sunday = Tier 3 day)")
            return []

        all_opps: list[dict] = []
        for query in queries:
            url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&sort=date"
            logger.info(f"[Tier2] Searching: '{query}'")
            text = self.scrape_dynamic(url, f"Indeed:{query[:30]}")
            if text:
                opps = self.parse_with_gemini(text, "Indeed", url)
                all_opps.extend(opps)
            time.sleep(3)

        self.stats["by_tier"]["rotation"] += len(all_opps)
        return all_opps

    # ==================================================================
    # TIER 3 — Program database scan (Sunday only)
    # ==================================================================

    def tier3_programs(self) -> list[dict]:
        if self.weekday != 6:
            logger.info("[Tier3] Skipping (not Sunday)")
            return []

        logger.info("[Tier3] Sunday — running program database scan")
        all_opps: list[dict] = []

        static_sites = {
            "NSF REU": "https://www.nsf.gov/crssprgm/reu/reu_search.jsp",
            "DOE SULI": "https://science.osti.gov/wdts/suli",
            "NSF GRFP": "https://www.nsfgrfp.org/",
            "Goldwater": "https://goldwaterscholarship.gov/",
            "DAAD RISE": "https://www.daad.de/rise/en/",
            "Amgen Scholars": "https://amgenscholars.com/",
            "HHMI": "https://www.hhmi.org/programs/science-education",
        }

        for name, url in static_sites.items():
            text = self.scrape_static(url, name)
            if text:
                opps = self.parse_with_gemini(text, name, url)
                all_opps.extend(opps)
            time.sleep(2)

        dynamic_sites = {
            "Pathways to Science": "https://www.pathwaystoscience.org/programs.aspx",
            "EURAXESS": "https://euraxess.ec.europa.eu/jobs/search",
        }

        for name, url in dynamic_sites.items():
            text = self.scrape_dynamic(url, name)
            if text:
                opps = self.parse_with_gemini(text, name, url)
                all_opps.extend(opps)
            time.sleep(2)

        self.stats["by_tier"]["programs"] += len(all_opps)
        return all_opps

    # ==================================================================
    # Main runner
    # ==================================================================

    def run(self) -> list[dict]:
        start = time.time()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        logger.info("=" * 60)
        logger.info(f"OpportunityHub Scraper v2 — {days[self.weekday]} {self.today}")
        logger.info("=" * 60)

        all_opps: list[dict] = []

        tiers = [
            ("Tier1: USAJobs API", self.tier1_usajobs),
            ("Tier1: Adzuna API", self.tier1_adzuna),
            ("Tier2: Search Rotation", self.tier2_rotation),
            ("Tier3: Program DB", self.tier3_programs),
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
            f"  By tier: API={self.stats['by_tier']['api']}, "
            f"Rotation={self.stats['by_tier']['rotation']}, "
            f"Programs={self.stats['by_tier']['programs']}"
        )
        logger.info("=" * 60)

        return unique


if __name__ == "__main__":
    scraper = OpportunityScraper()
    scraper.run()
