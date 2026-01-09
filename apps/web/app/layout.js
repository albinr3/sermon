import { Fraunces, Space_Grotesk } from "next/font/google";

import "./globals.css";
import ThemeToggle from "./components/ThemeToggle";
import Providers from "./providers";

export const metadata = {
  title: "SermonClip Studio",
  description: "Curate, clip, and publish sermons with clarity."
};

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap"
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap"
});

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      data-theme="light"
      className={`${spaceGrotesk.variable} ${fraunces.variable}`}
    >
      <body className="min-h-screen bg-[color:var(--bg)] text-[color:var(--ink)] antialiased">
        <Providers>
          <div className="fixed right-6 top-6 z-50">
            <ThemeToggle />
          </div>
          {children}
        </Providers>
      </body>
    </html>
  );
}
