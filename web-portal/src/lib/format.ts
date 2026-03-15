export function deadlineBadge(deadline: string): { text: string; cls: string } {
  if (!deadline || deadline === "Unknown")
    return { text: "TBD", cls: "bg-gray-100 text-gray-500" };
  if (deadline === "Rolling")
    return { text: "Rolling", cls: "bg-emerald-100 text-emerald-700" };
  const d = new Date(deadline + "T23:59:59");
  const diff = Math.ceil((d.getTime() - Date.now()) / 86_400_000);
  if (diff < 0) return { text: "Expired", cls: "bg-red-100 text-red-700" };
  if (diff <= 14) return { text: `D-${diff}`, cls: "bg-orange-100 text-orange-700" };
  if (diff <= 30) return { text: `D-${diff}`, cls: "bg-yellow-100 text-yellow-700" };
  return { text: deadline, cls: "bg-gray-100 text-gray-500" };
}

export function formatUpdatedDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);
  if (diffDays === 0) return "Updated today";
  if (diffDays === 1) return "Updated yesterday";
  if (diffDays < 7) return `Updated ${diffDays} days ago`;
  if (diffDays < 30) return `Updated ${Math.floor(diffDays / 7)} weeks ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function formatUpdatedDateFull(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}
