export interface Opportunity {
  id: string;
  organization: string;
  title: string;
  url: string;
  description: string;
  field: string;
  opportunity_type: string;
  year_level: string[];
  city: string | null;
  state: string | null;
  country: string;
  is_remote: boolean;
  deadline: string;
  start_date: string | null;
  duration: string | null;
  is_paid: boolean | null;
  compensation: string | null;
  source: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const FIELDS = [
  "Chemistry",
  "Biology",
  "Physics",
  "Computer Science",
  "Engineering",
  "Math",
  "Data Science",
  "Environmental Science",
  "Neuroscience",
  "Materials Science",
  "Biomedical",
  "Astronomy",
  "General STEM",
] as const;

export const FIELD_EMOJI: Record<string, string> = {
  Chemistry: "🧪",
  Biology: "🧬",
  Physics: "⚛️",
  "Computer Science": "💻",
  Engineering: "⚙️",
  Math: "📐",
  "Data Science": "📊",
  "Environmental Science": "🌿",
  Neuroscience: "🧠",
  "Materials Science": "🔬",
  Biomedical: "🏥",
  Astronomy: "🔭",
  "General STEM": "⚡",
};

export const OPPORTUNITY_TYPES = [
  "Research",
  "Internship",
  "Fellowship",
  "Scholarship",
  "Competition",
  "Conference",
  "Summer Program",
  "Co-op",
] as const;

export const TYPE_EMOJI: Record<string, string> = {
  Research: "🔬",
  Internship: "💼",
  Fellowship: "🎓",
  Scholarship: "🏆",
  Competition: "⚡",
  Conference: "🎤",
  "Summer Program": "☀️",
  "Co-op": "🔄",
};

export const TYPE_COLOR: Record<string, string> = {
  Research: "bg-blue-100 text-blue-700",
  Internship: "bg-emerald-100 text-emerald-700",
  Fellowship: "bg-purple-100 text-purple-700",
  Scholarship: "bg-amber-100 text-amber-700",
  Competition: "bg-red-100 text-red-700",
  Conference: "bg-teal-100 text-teal-700",
  "Summer Program": "bg-orange-100 text-orange-700",
  "Co-op": "bg-indigo-100 text-indigo-700",
};

export const TYPE_DESC: Record<string, string> = {
  Research: "REU programs, lab positions, thesis research",
  Internship: "Industry experience at top companies",
  Fellowship: "Funded research & leadership programs",
  Scholarship: "Merit & research-based financial awards",
  Competition: "Hackathons, olympiads, challenges",
  Conference: "Present research, network, learn",
  "Summer Program": "Intensive summer research experiences",
  "Co-op": "Extended industry rotations",
};

export const YEAR_LEVELS = [
  "Freshman",
  "Sophomore",
  "Junior",
  "Senior",
  "Graduate",
] as const;

export const YEAR_COLOR: Record<string, string> = {
  Freshman: "bg-sky-100 text-sky-700",
  Sophomore: "bg-emerald-100 text-emerald-700",
  Junior: "bg-amber-100 text-amber-700",
  Senior: "bg-purple-100 text-purple-700",
  Graduate: "bg-rose-100 text-rose-700",
  Any: "bg-gray-100 text-gray-600",
};

export const COUNTRY_FLAG: Record<string, string> = {
  USA: "🇺🇸",
  "United States": "🇺🇸",
  UK: "🇬🇧",
  "United Kingdom": "🇬🇧",
  Germany: "🇩🇪",
  Switzerland: "🇨🇭",
  France: "🇫🇷",
  Japan: "🇯🇵",
  "South Korea": "🇰🇷",
  China: "🇨🇳",
  Canada: "🇨🇦",
  Australia: "🇦🇺",
  Netherlands: "🇳🇱",
  Singapore: "🇸🇬",
  India: "🇮🇳",
};

export const LOCATION_GROUPS: Record<string, string[]> = {
  USA: ["USA", "United States"],
  Europe: ["UK", "United Kingdom", "Germany", "France", "Switzerland", "Netherlands", "Sweden", "Denmark", "Norway", "Italy", "Spain", "Austria", "Belgium"],
  Asia: ["Japan", "South Korea", "China", "Singapore", "India", "Taiwan", "Hong Kong"],
};
