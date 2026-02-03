import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "For You – Personalized X Recommendation",
  description: "Tunable feed powered by the X recommendation pipeline",
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
