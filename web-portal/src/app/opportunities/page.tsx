import { Suspense } from "react";
import type { Metadata } from "next";
import OpportunitiesContent from "./OpportunitiesContent";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export const metadata: Metadata = {
  title: "Opportunities — OpportunityHub",
  description: "Browse STEM research positions, internships, fellowships, scholarships, and more for college students in the USA and South Korea.",
};

export default function OpportunitiesPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl px-6 py-10">
          <h1 className="mb-6 text-3xl font-bold text-gray-900">Opportunities</h1>
          <LoadingSkeleton />
        </div>
      }
    >
      <OpportunitiesContent />
    </Suspense>
  );
}
