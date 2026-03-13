import type { Metadata } from "next";
import AboutContent from "./AboutContent";

export const metadata: Metadata = {
  title: "About — OpportunityHub",
  description: "Learn how OpportunityHub aggregates STEM opportunities for college students using AI-powered scraping.",
};

export default function AboutPage() {
  return <AboutContent />;
}
