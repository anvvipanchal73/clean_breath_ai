import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Phase 0: Enable progressive web app via next-pwa in Phase 1
  // For now we include the manifest and service worker manually
  experimental: {},
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          // Security headers
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          // Allow service worker at root scope
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
    ];
  },
};

export default nextConfig;
