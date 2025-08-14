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
  title: 'saber的个人网站',
  description: '全栈开发 | 用代码构建美好数字世界',
  author: 'saber',

  // 联系信息
  contact: {
    email: 'contact@example.com',
    phone: '', // 如果需要添加电话号码
  },

  // 社交媒体信息
  social: {
    github: {
      username: 'username',
      url: 'https://github.com/username'
    },
    linkedin: {
      username: 'username',
      url: 'https://linkedin.com/in/username'
    },
    twitter: {
      username: 'username',
      url: 'https://twitter.com/username'
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
