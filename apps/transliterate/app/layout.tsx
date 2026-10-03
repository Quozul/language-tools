import { cn } from "cn";
import { Geist } from "next/font/google";
import type { ReactNode } from "react";
import { Toaster } from "@qzl/ui/components/toast";
import { TooltipProvider } from "@qzl/ui/components/tooltip";
import "@qzl/ui/globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" className={cn("dark font-sans", geist.variable)}>
      <body>
        <TooltipProvider>
          {children}
          <Toaster />
        </TooltipProvider>
      </body>
    </html>
  );
}
