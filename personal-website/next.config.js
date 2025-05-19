/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
    // 允许未优化的图片，用于开发环境
    unoptimized: process.env.NODE_ENV === 'development',
  },
}

module.exports = nextConfig
