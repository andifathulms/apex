/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // DRF requires trailing slashes, but Next strips the trailing slash from
  // :path* when building the rewrite destination — so Django would 301 it back
  // and the two loop. skipTrailingSlashRedirect stops Next from bouncing the
  // client, and we re-append the slash on the destination so Django receives
  // e.g. /api/seasons/ intact. (All client API paths end in a slash.)
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // Proxy API calls to Django in local dev so the browser can hit /api/*.
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*/",
        destination: `${apiBase}/api/:path*/`,
      },
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*/`,
      },
    ];
  },
};

export default nextConfig;
