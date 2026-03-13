"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { getBookmarks } from "@/lib/bookmarks";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/saved", label: "Saved" },
  { href: "/about", label: "About" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [bookmarkCount, setBookmarkCount] = useState(0);
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    setBookmarkCount(getBookmarks().length);
    const handler = () => setBookmarkCount(getBookmarks().length);
    window.addEventListener("bookmarks-changed", handler);
    return () => window.removeEventListener("bookmarks-changed", handler);
  }, []);

  useEffect(() => {
    if (!open) return;
    function handleClickOutside(e: MouseEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <nav ref={navRef} className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md">
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
              className={`relative text-sm font-medium transition-colors ${
                pathname === l.href ? "text-blue-600" : "text-gray-600 hover:text-blue-500"
              }`}
            >
              {l.label}
              {l.href === "/saved" && bookmarkCount > 0 && (
                <span className="absolute -right-4 -top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-600 px-1 text-[10px] font-bold text-white">
                  {bookmarkCount}
                </span>
              )}
            </Link>
          ))}
        </div>

        <button onClick={() => setOpen(!open)} className="flex flex-col gap-1 md:hidden" aria-label="Menu" aria-expanded={open}>
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
              className={`flex items-center justify-between py-3 text-sm font-medium ${
                pathname === l.href ? "text-blue-600" : "text-gray-600"
              }`}
            >
              {l.label}
              {l.href === "/saved" && bookmarkCount > 0 && (
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-blue-600 px-1.5 text-[11px] font-bold text-white">
                  {bookmarkCount}
                </span>
              )}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
