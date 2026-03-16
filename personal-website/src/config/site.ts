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
  title: '许辉的个人网站',
  description:
    '7年经验全栈开发工程师，做过 Vue、UniApp、PHP、ThinkPHP、MySQL、Redis 等项目，重点落在企业后台、系统对接和复杂业务落地。',
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
  // techStack: 'Vue / UniApp / PHP / ThinkPHP / MySQL / Redis / Next.js',
  profile: {
    briefIntro:
      '我是许辉，一名做过前端、后端和跨端项目的全栈开发工程师。近几年除了 Vue、UniApp 和后台系统开发，也持续参与 PHP、ThinkPHP、MySQL、Redis 相关项目，重点处理企业后台、系统对接和复杂业务场景。',
    aboutIntro: [
      '你好，我是许辉，一名拥有 8 年项目经验的全栈开发工程师。近几年主要做企业后台系统、小程序项目、系统对接和复杂业务交付。',
      '技术上我主要使用 Vue2 / Vue3、UniApp、React、Next.js，也做过 PHP、ThinkPHP、Node.js、MySQL、Redis 相关项目，能从前端页面一路推进到接口、数据结构和后台流程。',
      '我参与过医院 SaaS、企业小程序、福利商城、数据同步中台、官网后台等多类项目，做过团队协作开发，也独立负责过完整交付。',
      '相比单纯页面开发，我更擅长把复杂业务落成可运行、可维护的系统，包括权限、动态表单、数据同步、支付链路、日志排查和后台配置能力。',
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
        title: '框架与交付',
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
          '负责用户管理、档案管理、评价体系等核心模块前端开发。',
          '设计并落地 JSON 驱动的动态表单能力，提升复杂表单开发效率。',
          '开发 Node.js 中间层调试工具，改善前后端分离场景下的联调效率。',
          '参与团队技术规范、代码评审和新人培养，推动前端协作方式稳定化。',
        ],
        techStack: 'Vue2 / Vue3、Element UI、TypeScript、Node.js',
      },
      {
        role: '全栈开发工程师',
        company: '上海饰百秀网络科技有限公司',
        period: '2021.09 - 2022.05',
        project: '建筑装修项目管理系统',
        highlights: [
          '独立完成系统架构、数据库、接口和前端页面设计。',
          '同时交付 PC 管理端和 UniApp 移动端，覆盖现场管理场景。',
          '实现复杂 Excel 批量导入和甘特图交互组件，支撑项目计划管理。',
          '通过离线缓存与数据同步提升现场作业效率。',
        ],
        techStack: 'Vue3、Ant Design、UniApp、Node.js、Express、MySQL',
      },
      {
        role: '全栈开发工程师',
        company: '上海国芮信息科技有限公司',
        period: '2019.10 - 2021.06',
        project: '数字货币交易平台后台管理系统',
        highlights: [
          '参与用户、营销、理财、权限等核心后台模块建设。',
          '设计多角色权限体系和数据可视化看板，支撑运营管理。',
          '建立系统监控与预警能力，保障平台稳定运行。',
          '通过性能优化缩短页面加载与接口响应时间。',
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
          '积累了完整的独立交付与问题解决经验。',
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
