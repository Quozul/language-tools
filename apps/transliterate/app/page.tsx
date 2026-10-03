import type { Metadata, Viewport } from "next";
import { TransliterateApp } from "@/components/transliterate";

export const metadata: Metadata = {
  title: "Transliterate",
};

export const viewport: Viewport = {
  themeColor: "#000000",
  colorScheme: "dark",
};

export default function Home() {
  return <TransliterateApp />;
}
