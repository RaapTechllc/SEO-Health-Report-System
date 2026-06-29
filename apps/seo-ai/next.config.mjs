/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Audit fetching happens server-side in route handlers.
  experimental: {
    serverActions: {
      bodySizeLimit: "2mb",
    },
  },
};

export default nextConfig;
