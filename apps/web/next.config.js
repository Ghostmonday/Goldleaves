/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  env: {
    NEXT_PUBLIC_USE_LIVE_USAGE: process.env.NEXT_PUBLIC_USE_LIVE_USAGE,
    USAGE_RATE_CENTS: process.env.USAGE_RATE_CENTS,
  },
}

module.exports = nextConfig