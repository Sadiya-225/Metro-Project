import type { Metadata } from "next";
import "./globals.css";
import { AlertProvider } from "@/components/AlertProvider";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

export const metadata: Metadata = {
  title: "Metro Route Intelligence",
  description: "AI-powered Hyderabad Metro route optimization and delay intelligence dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("h-full antialiased", "font-sans", geist.variable)}>
      <body className="min-h-full flex flex-col">
        <AlertProvider>{children}</AlertProvider>
      </body>
    </html>
  );
}
