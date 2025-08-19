/**
 * site.ts
 *
 * 描述：网站全局配置文件，存储网站的通用配置信息
 *
 * 功能：
 * - 提供网站的基本信息（标题、描述等）
 * - 提供联系信息（电子邮件、社交媒体等）
 * - 提供其他全局配置项
 *
 * 主要接口/常量：
 * - siteConfig：网站配置对象
 *
 * 导出：
 * - siteConfig 对象（默认导出）
 */

// 网站配置对象
export const siteConfig = {
  // 基本信息
  title: '许辉的个人网站',
  description: '7年经验全栈开发工程师 | Vue.js + React + Next.js + Node.js',
  author: '许辉',

  // 联系信息
  contact: {
    email: 'weiaijie@outlook.com',
    phone: '18930523857',
    location: '上海',
  },

  // 社交媒体信息
  social: {
    github: {
      username: 'xuhui',
      url: 'https://github.com/xuhui'
    },
    linkedin: {
      username: 'xuhui',
      url: 'https://linkedin.com/in/xuhui'
    },
    wechat: {
      username: 'xuhui_dev',
      qrcode: '/images/wechat-qr.png'
    }
  },

  // 版权信息
  copyright: {
    text: '保留所有权利',
    startYear: 2023, // 如果需要显示版权年份范围，例如 2023-2024
  },

  // 技术栈信息
  techStack: '使用 Next.js、React 和 TypeScript 构建',
};

export default siteConfig;
