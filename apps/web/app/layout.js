import "./globals.css";
import Providers from "./providers";

export const metadata = {
  title: "Sermon MVP",
  description: "Sermon transcript to clip"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
