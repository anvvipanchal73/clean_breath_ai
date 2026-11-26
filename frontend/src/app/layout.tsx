import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CleanBreath AI",
  description:
    "Air quality guidance for families – low-emission routines, indoor air tips, and community action.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "CleanBreath",
  },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  themeColor: "#1565C0",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        {/* Register service worker via inline script – avoids next/script async issues with SW */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js', { scope: '/' })
                    .catch(function(err) { console.warn('SW registration failed:', err); });
                });
              }
            `,
          }}
        />
      </head>
      <body className="bg-cb-bg text-cb-text font-sans antialiased min-h-screen">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-cb-primary text-white px-4 py-2 rounded-xl z-50"
        >
          Skip to main content
        </a>
        <main id="main-content" className="max-w-md mx-auto pb-safe-bottom">
          {children}
        </main>
      </body>
    </html>
  );
}
