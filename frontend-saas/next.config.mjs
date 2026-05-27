/** @type {import('next').NextConfig} */
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig = {
  // Docker: يُضبط DOCKER_BUILD=true في build args → standalone mode
  // Netlify / Vercel: لا يُضبط → بناء عادي
  ...(process.env.DOCKER_BUILD === "true" ? { output: "standalone" } : {}),
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
