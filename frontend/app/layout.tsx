import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Quantum Heist — Echo Console",
  description: "Plan the heist, fork the timeline, collapse what fails.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
