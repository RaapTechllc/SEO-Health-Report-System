import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rankwise — AI-Age SEO Audit",
  description:
    "Audit your site for technical SEO, content authority, and visibility across AI answer engines like ChatGPT, Claude, Perplexity and Gemini.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
