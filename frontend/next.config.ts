import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle (.next/standalone) for the Docker runner.
  output: "standalone",

  // Proxy API and WS to backend (matches Vite dev proxy)
  async rewrites() {
    let simulatorUrl = process.env.SIMULATOR_URL || "http://localhost:8082";
    if (simulatorUrl.includes("${")) {
        simulatorUrl = "http://localhost:8082";
    }
    return [
      { source: "/api/v1/:path*", destination: `${simulatorUrl}/api/v1/:path*` },
      { source: "/api/:path*", destination: `${simulatorUrl}/api/v1/:path*` },
    ];
  },

  // Turbopack resolve alias for mapbox-gl (SSR compatibility)
  turbopack: {
    resolveAlias: {
      "mapbox-gl": "mapbox-gl/dist/mapbox-gl.js",
    },
  },

  // Webpack alias for mapbox-gl (production builds)
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "mapbox-gl$": "mapbox-gl/dist/mapbox-gl.js",
    };
    return config;
  },

  // Allow map tile domains
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "api.mapbox.com",
        pathname: "/styles/**",
      },
      {
        protocol: "https",
        hostname: "unpkg.com",
      },
    ],
  },
};

export default nextConfig;
