/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // 图片优化配置
  images: {
    domains: ['localhost'],
    // 允许未优化的图片，用于开发环境
    unoptimized: process.env.NODE_ENV === 'development',
    // 图片格式优化
    formats: ['image/webp', 'image/avif'],
    // 设备尺寸
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    // 图片尺寸
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // 编译优化
  compiler: {
    // 移除console.log（仅生产环境）
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // 实验性功能
  experimental: {
    // 启用应用目录（Next.js 13+）
    // appDir: true,
  },

  // 压缩配置
  compress: true,

  // 生产环境优化
  ...(process.env.NODE_ENV === 'production' && {
    // 生产环境下的额外配置
    poweredByHeader: false,
    generateEtags: true,

    // 重定向配置
    async redirects() {
      return [
        // 可以在这里添加重定向规则
      ];
    },

    // 头部配置
    async headers() {
      return [
        {
          source: '/(.*)',
          headers: [
            {
              key: 'X-Frame-Options',
              value: 'DENY',
            },
            {
              key: 'X-Content-Type-Options',
              value: 'nosniff',
            },
            {
              key: 'Referrer-Policy',
              value: 'origin-when-cross-origin',
            },
          ],
        },
        {
          source: '/images/(.*)',
          headers: [
            {
              key: 'Cache-Control',
              value: 'public, max-age=31536000, immutable',
            },
          ],
        },
      ];
    },
  }),
}

module.exports = nextConfig
