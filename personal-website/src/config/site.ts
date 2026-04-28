export interface ProfileSkillGroup {
  title: string;
  items: string[];
}

export interface ProfileExperience {
  role: string;
  company: string;
  period: string;
  project: string;
  highlights: string[];
  techStack: string;
}

export interface ProfileEducation {
  degree: string;
  school: string;
  period: string;
}

export const siteConfig = {
  siteUrl: 'https://blog.weiaijie.top',
  title: '许辉 - 全栈开发工程师',
  description:
    '许辉的个人网站，整理一些做过的后台、小程序、官网和系统对接项目。',
  author: '许辉',
  age: 29,
  currentLocation: '铜陵',
  targetLocation: '上海',
  contact: {
    email: 'weiaijie@outlook.com',
    phone: '18930523857',
    location: '上海',
  },
  social: {
    github: {
      username: 'weiaijie',
      url: 'https://github.com/weiaijie',
    },
    linkedin: {
      username: 'xuhui',
      url: 'https://linkedin.com/in/xuhui',
    },
    twitter: {
      username: '',
      url: '',
    },
    wechat: {
      username: 'xuhui_dev',
      qrcode: '/images/wechat-qr.png',
    },
  },
  copyright: {
    text: '保留所有权利。',
    startYear: 2018,
  },
  techStack: 'Vue / UniApp / PHP / ThinkPHP / MySQL / Redis / Next.js',
  profile: {
    heroRole: '全栈开发工程师',
    heroSummary: [
      '主要做企业后台、小程序、官网和系统对接类项目',
      '也会记录一些项目里遇到的问题和处理方式',
    ],
    briefIntro:
      '我是许辉，一名全栈开发工程师，主要做企业后台、小程序、官网展示站、系统对接和中小型业务系统。平时也会用 Codex、OpenCode、Claude Code 这类工具辅助写代码、查问题和整理资料，但项目怎么改、质量怎么样，还是我自己负责。',
    aboutIntro: [
      '你好，我是许辉，一名全栈开发工程师，目前主要做企业后台、小程序、官网展示站、系统对接和中小型业务系统。',
      '我可以自己处理前端页面、接口、数据库和基础部署，也可以配合团队接手功能迭代、问题修复和旧项目调整。比起只把页面做出来，我更在意后面好不好维护、出问题能不能查。',
      '技术上我主要使用 Vue2 / Vue3、UniApp、React、Next.js，也做过 PHP、ThinkPHP、Node.js、MySQL、Redis 相关项目。接触过医院培训系统、企业小程序、福利商城、数据同步、官网后台等项目。',
      '现在开发时我也会用 Codex、OpenCode、Claude Code 这类 AI 工具辅助整理需求、写代码和排查问题。但工具只是辅助，项目怎么改、代码能不能长期维护，还是我自己来判断。',
    ],
    skillGroups: [
      {
        title: '前端与跨端',
        items: ['Vue2', 'Vue3', 'UniApp', 'React', 'Next.js'],
      },
      {
        title: '后端与数据',
        items: ['PHP', 'ThinkPHP', 'Node.js', 'Express', 'MySQL', 'Redis'],
      },
      {
        title: '框架与工具',
        items: ['CRMEB', 'Element UI', 'Ant Design', 'uView', 'Vite', 'Webpack', 'ECharts', 'Nginx', 'Docker', '宝塔'],
      },
    ] as ProfileSkillGroup[],
    experience: [
      {
        role: '前端开发工程师',
        company: '上海墨安信息科技有限公司',
        period: '2022.06 - 2025.01',
        project: '医院教育管理 SaaS 系统',
        highlights: [
          '负责用户管理、档案管理、评价体系等模块的前端开发。',
          '做过 JSON 驱动的动态表单，减少重复表单页面开发。',
          '开发过 Node.js 联调工具，方便前后端分离项目排查问题。',
          '参与代码评审和新人带教，整理过一些团队常用写法。',
        ],
        techStack: 'Vue2 / Vue3、Element UI、TypeScript、Node.js',
      },
      {
        role: '全栈开发工程师',
        company: '上海饰百秀网络科技有限公司',
        period: '2021.09 - 2022.05',
        project: '建筑装修项目管理系统',
        highlights: [
          '独立完成数据库、接口、后台页面和移动端开发。',
          '同时做 PC 管理端和 UniApp 移动端，处理现场管理相关流程。',
          '实现复杂 Excel 批量导入和甘特图交互组件。',
          '给移动端做过离线缓存和数据同步处理。',
        ],
        techStack: 'Vue3、Ant Design、UniApp、Node.js、Express、MySQL',
      },
      {
        role: '全栈开发工程师',
        company: '上海国芮信息科技有限公司',
        period: '2019.10 - 2021.06',
        project: '数字货币交易平台后台管理系统',
        highlights: [
          '参与用户、营销、理财、权限等后台模块开发。',
          '做过多角色权限和数据看板相关功能。',
          '参与系统监控、预警和一些性能问题处理。',
          '长期在运营后台里改功能、修问题。',
        ],
        techStack: 'Vue2、Element UI、ECharts、Node.js、Express、MySQL、Redis',
      },
      {
        role: 'Web 开发工程师',
        company: '上海欧莱美医疗美容医院有限公司',
        period: '2018.05 - 2019.08',
        project: '医疗美容官网与商品展示系统',
        highlights: [
          '独立完成官网前端开发与商品展示系统搭建。',
          '实现分类、检索、详情展示和后台内容管理。',
          '在医疗行业规范约束下兼顾展示效果与内容合规。',
          '这段经历让我比较早接触到从页面到后台再到上线的完整流程。',
        ],
        techStack: 'JavaScript、Vue、HTML/CSS、ThinkPHP、MySQL',
      },
    ] as ProfileExperience[],
    education: {
      degree: '大专 · 计算机应用技术',
      school: '上海中侨职业技术学院',
      period: '2015.09 - 2018.06',
    } as ProfileEducation,
  },
};

export default siteConfig;
