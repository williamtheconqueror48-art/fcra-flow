import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FCRA FLOW — Foreign Funding Disclosure Tracker",
  description:
    "A public-interest OSINT tracker of India's FCRA Form FC-4 foreign-funding disclosures: NGO recipients, foreign donors, amounts and years, with mechanical, fully-disclosed anomaly flags. Every figure traces to a cited public source; nothing editorialized.",
  openGraph: {
    title: "FCRA FLOW — Foreign Funding Disclosure Tracker",
    description:
      "Form FC-4 public filings, mechanically flagged. Every figure traces to a cited source; nothing editorialized.",
    url: "https://fcra-flow.vercel.app",
    siteName: "FCRA FLOW",
    images: [
      {
        url: "https://fcra-flow.vercel.app/og-image.png",
        width: 2240,
        height: 1120,
        alt: "FCRA FLOW — Foreign Funding Disclosure Tracker",
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "FCRA FLOW — Foreign Funding Disclosure Tracker",
    description:
      "Form FC-4 public filings, mechanically flagged. Every figure traces to a cited source.",
    images: ["https://fcra-flow.vercel.app/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
