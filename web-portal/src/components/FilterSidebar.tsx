"use client";

import { FIELDS, OPPORTUNITY_TYPES, YEAR_LEVELS } from "@/lib/types";
import SearchBar from "./SearchBar";

interface FilterState {
  q: string;
  fields: string[];
  types: string[];
  years: string[];
  locations: string[];
  paidOnly: boolean;
  sort: "newest" | "deadline";
}

interface Props {
  filters: FilterState;
  onChange: (f: FilterState) => void;
  onReset: () => void;
  resultCount: number;
  mobileOpen: boolean;
  onToggleMobile: () => void;
}

const LOCATION_OPTIONS = ["USA", "South Korea", "Remote"];

function CheckboxGroup({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: readonly string[] | string[];
  selected: string[];
  onChange: (v: string[]) => void;
}) {
  const toggle = (v: string) => {
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v]);
  };

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</p>
      <div className="space-y-1.5">
        {options.map((o) => (
          <label key={o} className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={selected.includes(o)}
              onChange={() => toggle(o)}
              className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            {o}
          </label>
        ))}
      </div>
    </div>
  );
}

export default function FilterSidebar({ filters, onChange, onReset, resultCount, mobileOpen, onToggleMobile }: Props) {
  const update = (partial: Partial<FilterState>) => onChange({ ...filters, ...partial });

  const content = (
    <div className="space-y-6">
      <SearchBar value={filters.q} onChange={(q) => update({ q })} />

      <CheckboxGroup label="📚 Field" options={FIELDS} selected={filters.fields} onChange={(fields) => update({ fields })} />
      <CheckboxGroup label="📋 Type" options={OPPORTUNITY_TYPES} selected={filters.types} onChange={(types) => update({ types })} />
      <CheckboxGroup label="🎓 Year Level" options={YEAR_LEVELS} selected={filters.years} onChange={(years) => update({ years })} />
      <CheckboxGroup label="🌍 Location" options={LOCATION_OPTIONS} selected={filters.locations} onChange={(locations) => update({ locations })} />

      {/* Paid toggle */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">💰 Compensation</p>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={filters.paidOnly}
            onChange={() => update({ paidOnly: !filters.paidOnly })}
            className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Paid only
        </label>
      </div>

      {/* Sort */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">Sort</p>
        <div className="flex gap-2">
          {(["newest", "deadline"] as const).map((s) => (
            <button
              key={s}
              onClick={() => update({ sort: s })}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                filters.sort === s ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {s === "newest" ? "Newest" : "Deadline"}
            </button>
          ))}
        </div>
      </div>

      <button onClick={onReset} className="w-full rounded-lg border border-gray-300 py-2 text-xs font-medium text-gray-500 transition-colors hover:bg-gray-100">
        Clear all filters
      </button>

      <p className="text-center text-sm text-gray-500">
        Showing <strong className="text-blue-600">{resultCount}</strong> opportunities
      </p>
    </div>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button onClick={onToggleMobile} className="mb-4 flex w-full items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-700 lg:hidden">
        <span>Filters {resultCount > 0 && `(${resultCount})`}</span>
        <span className={`transition-transform ${mobileOpen ? "rotate-180" : ""}`}>▾</span>
      </button>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 lg:hidden">{content}</div>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden w-[280px] shrink-0 lg:block">
        <div className="sticky top-[81px] max-h-[calc(100vh-100px)] overflow-y-auto rounded-xl border border-gray-200 bg-white p-5">
          {content}
        </div>
      </aside>
    </>
  );
}
