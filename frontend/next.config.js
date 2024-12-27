/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: [],
  },
  // Enable experimental features if needed
  experimental: {
    // serverActions: true,
  },
  // Configure webpack if needed
  webpack: (config, { isServer }) => {
    // Add custom webpack configurations here
    return config;
  },
}

module.exports = nextConfig 