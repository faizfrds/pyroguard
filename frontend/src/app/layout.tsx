import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PyroGuard AI | Indonesia Wildfire & Peatland Intelligence",
  description: "Real-time radar & optical multi-sensor agent for tropical peatland wildfire intelligence in Indonesia.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080c14] text-gray-100 min-h-screen flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}

