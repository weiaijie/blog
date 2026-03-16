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
    '7年经验全栈开发工程师，专注前端技术与复杂业务系统落地，具备 Vue 生态、Node.js 和跨端开发经验。',
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
  techStack: '使用 Next.js、React 和 TypeScript 构建',
  profile: {
    briefIntro:
      '我是许辉，一名专注前端体验与复杂业务系统建设的全栈开发工程师。长期深耕 Vue 生态，也具备 Node.js、UniApp 和 Next.js 项目落地经验，参与过医院 SaaS、金融交易、工程管理和企业官网等多类项目。',
    aboutIntro: [
      '你好，我是许辉，一名以前端为核心能力的全栈开发工程师，拥有 7 年项目开发经验。长期负责复杂后台系统、SaaS 平台和跨端应用的方案设计与交付。',
      '技术上我深度使用 Vue2 / Vue3、TypeScript、JavaScript ES6+，熟悉 Element UI、Ant Design、Vant、uView 等组件体系，也能独立完成 Node.js、Express、MySQL、Redis 等后端配套开发。',
      '我参与过医院教育 SaaS、数字货币交易平台、建筑项目管理系统、医疗美容官网等项目，既做过大型团队协作，也独立负责过全栈交付，能够从业务抽象、架构设计到落地实施完整推进。',
      '我重视代码质量、可维护性和用户体验，做过动态表单、权限系统、数据同步、性能优化等关键能力建设，也有带新人、做技术规范和推进团队协作的经验。',
    ],
    skillGroups: [
      {
        title: '前端开发',
        items: ['Vue2', 'Vue3', 'TypeScript', 'JavaScript', 'React', 'Next.js', 'UniApp'],
      },
      {
        title: 'UI 与工程化',
        items: ['Element UI', 'Ant Design', 'Vant', 'uView', 'Webpack', 'Vite', 'ECharts'],
      },
      {
        title: '后端与基础设施',
        items: ['Node.js', 'Express', 'MySQL', 'Redis', 'ThinkPHP', 'Linux', 'Nginx'],
      },
    ] as ProfileSkillGroup[],
    experience: [
      {
        role: '前端开发工程师',
        company: '上海墨安信息科技有限公司',
        period: '2022.06 - 2024.10',
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
