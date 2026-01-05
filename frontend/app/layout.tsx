import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"
import { Suspense } from "react"
import { ThemeProvider } from "@/components/theme-provider"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
})

export const metadata: Metadata = {
  title: "Ronin Ecosystem Tracker",
  description: "Real-time blockchain analytics for the Ronin gaming ecosystem",
  generator: 'v0.app'
}

import { SWRProvider } from "@/components/swr-provider"

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`font-sans ${inter.variable}`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <SWRProvider>
            <Suspense fallback={null}>{children}</Suspense>
          </SWRProvider>
        </ThemeProvider>
        <Analytics />
        <script dangerouslySetInnerHTML={{
          __html: `
          (function() {
            function removeBadge() {
              const selectors = [
                'a[href*="v0.dev"]',
                'a[href*="v0"]',
                'iframe[src*="v0"]',
                '[data-v0-badge]',
                '[data-v0]'
              ];
              selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                  el.style.display = 'none';
                  el.remove();
                });
              });
            }
            if (document.readyState === 'loading') {
              document.addEventListener('DOMContentLoaded', removeBadge);
            } else {
              removeBadge();
            }
            setInterval(removeBadge, 500);
          })();
        `}} />
      </body>
    </html>
  )
}
