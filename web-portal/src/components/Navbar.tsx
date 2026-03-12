"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/about", label: "About" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-xl font-bold text-blue-600">
          <span>⚡</span>
          OpportunityHub
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`text-sm font-medium transition-colors ${
                pathname === l.href ? "text-blue-600" : "text-gray-600 hover:text-blue-500"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>

        <button onClick={() => setOpen(!open)} className="flex flex-col gap-1 md:hidden" aria-label="Menu">
          <span className={`block h-0.5 w-5 bg-gray-700 transition-transform ${open ? "translate-y-1.5 rotate-45" : ""}`} />
          <span className={`block h-0.5 w-5 bg-gray-700 transition-opacity ${open ? "opacity-0" : ""}`} />
          <span className={`block h-0.5 w-5 bg-gray-700 transition-transform ${open ? "-translate-y-1.5 -rotate-45" : ""}`} />
        </button>
      </div>

      {open && (
        <div className="border-t border-gray-100 bg-white px-6 pb-4 md:hidden">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className={`block py-3 text-sm font-medium ${
                pathname === l.href ? "text-blue-600" : "text-gray-600"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
