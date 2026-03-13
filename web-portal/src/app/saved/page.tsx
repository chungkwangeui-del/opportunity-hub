import type { Metadata } from "next";
import SavedContent from "./SavedContent";

export const metadata: Metadata = {
  title: "Saved — OpportunityHub",
  description: "Your bookmarked STEM opportunities, stored locally in your browser.",
};

export default function SavedPage() {
  return <SavedContent />;
}
