import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "OpportunityHub — STEM Opportunities for Students",
  description:
    "Every STEM opportunity in one place. Research, internships, fellowships, scholarships, and more — updated daily for college students worldwide.",
  keywords: [
    "STEM internship",
    "research opportunity",
    "REU",
    "fellowship",
    "scholarship",
    "college students",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${jakarta.variable} antialiased`} style={{ fontFamily: "var(--font-jakarta), sans-serif" }}>
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
