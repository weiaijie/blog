export interface ProjectSection {
  title: string;
  items: string[];
}

export interface ProjectCaseStudy {
  id: string;
  title: string;
  subtitle: string;
  category: string;
  categoryLabel: string;
  year: string;
  summary: string;
  positioning: string;
  tags: string[];
  highlights: string[];
  links: {
    label: string;
    url: string;
  }[];
  sections: ProjectSection[];
}

export const projectCategories = [
  { id: 'all', name: '全部案例' },
  { id: 'integration', name: '系统对接' },
  { id: 'mini-program', name: '小程序' },
  { id: 'commerce', name: '电商改造' },
  { id: 'enterprise', name: '企业系统' },
  { id: 'web', name: '网站与作品集' },
] as const;

export const projectCaseStudies: ProjectCaseStudy[] = [
  {
    id: 'xiangyi-benefit-mall',
    title: '香溢金联企业福利商城与供应商分账',
    subtitle: '基于 CRMEB PRO 的企业福利商城与供应商结算二开项目',
    category: 'commerce',
    categoryLabel: '电商改造',
    year: '2025.11 - 2026.02.14 / CRMEB PRO / ThinkPHP 8',
    summary:
      '基于 CRMEB PRO 商城进行二次开发，围绕企业采购、员工福利消费、供应商结算、组合支付和平台管理展开，完成企业福利场景下的商城业务改造与支付结算链路设计。项目上线后也持续承接维护与小范围迭代。',
    positioning:
      '这个项目本质上是 CRMEB PRO 的深度二开，不是简单换皮，而是把企业后台、员工端、平台端和供应商端打通，形成可落地、可运营、可对账、可继续维护的企业福利业务系统。',
    tags: ['CRMEB PRO', 'ThinkPHP 8', 'MySQL', 'Redis', 'Swoole', '组合支付', '供应商分账'],
    highlights: ['CRMEB PRO 二开', '企业客户体系', '组合支付链路', '持续维护与迭代'],
    links: [
      { label: '访问测试环境', url: 'https://test.wx.sunnycloudtop.com/' },
      { label: '访问正式地址', url: 'https://wx.sunnycloudtop.com/' },
    ],
    sections: [
      {
        title: '项目概述',
        items: [
          '这是一个基于 CRMEB PRO 的企业福利商城二开改造项目。',
          '核心场景包括企业采购、员工福利消费、组合支付和供应商结算。',
          '难点集中在多角色权限、资金流转、分账逻辑和退款回滚一致性。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '搭建企业客户、员工福利金和商品企业权限体系。',
          '重构组合支付流程，把即时扣款改成延迟确认，降低支付失败风险。',
          '重做供应商分账、平台补贴和退款流水逻辑，保证账务一致。',
          '项目交付后继续跟进使用过程中的细节修改、问题修复和业务调整。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '基于 CRMEB PRO 与 ThinkPHP 8 完成结构化业务扩展。',
          '亮点在于组合支付、供应商分账和退款回滚的一致性设计。',
          '体现了复杂业务系统、交易链路设计以及后续维护和迭代支持经验。',
        ],
      },
    ],
  },
  {
    id: 'ebmpapst-mini-program',
    title: '依必安派特大中华区小程序与后台管理系统',
    subtitle: '企业级会员运营、内容服务与后台配置一体化项目',
    category: 'mini-program',
    categoryLabel: '小程序 / 后台一体化',
    year: '2025.10 - 2025.11中旬 / uni-app / Vue 3 / Vue',
    summary:
      '这是依必安派特大中华区的前后台一体化项目，面向企业会员、经销商和潜在客户，前台小程序融合会员运营、内容分发、活动管理、业务申请、销售支持与 AI 导览能力，后台则承担内容管理、活动配置、业务表单处理、权限控制和数据运营支撑。项目交付后也持续承接问题修复和细节调整。',
    positioning:
      '这个项目不是单一品牌展示型小程序，也不是孤立后台，而是把品牌内容、用户身份体系、积分激励、活动报名、资料中心、业务咨询和后台配置体系统一成一个可持续运营的前后台闭环。',
    tags: ['uni-app', 'Vue 3', 'Vite', 'uview-plus', 'Vue', '微信登录', '动态表单', '后台配置'],
    highlights: ['小程序与后台一体化', '会员中心', '权限标签驱动', '持续维护迭代'],
    links: [{ label: '查看后台', url: 'https://yibiante.test.weiseo.com/' }],
    sections: [
      {
        title: '项目概述',
        items: [
          '这是一个面向会员、经销商和潜在客户的企业服务型项目，包含微信小程序前台和运营后台两部分。',
          '前台整合会员中心、内容中心、活动报名、业务申请和 AI 导览，后台承接内容发布、活动配置、资料管理和权限控制。',
          '项目体现了企业级会员运营、内容服务与后台支撑一体化能力。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '基于 uni-app + Vue 3 + Vite 开发，采用分包架构和统一请求层。',
          '梳理首页导航、会员中心、活动报名、资料中心和 AI 助手等前台模块，同时配套建设后台配置与运营支撑能力。',
          '通过权限标签、静默登录、动态表单和内容检索支撑持续运营。',
          '围绕内容中心、活动中心、表单中心和权限体系梳理后台能力，让前台功能可以由后台做配置与维护。',
          '上线后继续配合处理线上反馈、细节优化和一些小功能改动。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '把内容触达、活动运营、商机收集和用户沉淀放到同一入口中，并通过后台配置能力支撑长期运营。',
          '亮点包括分包结构、权限控制、动态表单、AI 问答以及前后台联动。',
          '同时体现了企业微信小程序、运营后台一体化建设和持续维护能力。',
        ],
      },
    ],
  },
  {
    id: 'maoju-dental-sync',
    title: '茂菊口腔',
    subtitle: '基于 CRMEB 的口腔小程序与诊所系统数据打通二开项目',
    category: 'integration',
    categoryLabel: '系统对接',
    year: '2025.08 - 2025.09 / ThinkPHP 6 / CRMEB',
    summary:
      '基于 CRMEB 小程序体系进行二次开发，围绕茂菊口腔与轻松牙医系统之间的数据流，搭建了一套可持续运行的数据同步体系，覆盖用户、预约、积分、默认医生创建、异常修复、定时任务和后台管理。项目交付后也一直持续维护，日常会结合日志排查问题并处理小改动。',
    positioning:
      '这个项目不是从零开发的小程序，而是基于 CRMEB 做业务二开，把诊所侧患者、预约、积分数据与小程序侧用户、订单稳定联动起来，形成可运行、可排查、可维护、可持续迭代的数据同步闭环。',
    tags: ['PHP 7.4', 'ThinkPHP 6', 'Vue 2', 'MySQL', 'Redis', 'CRMEB', '异步队列'],
    highlights: ['CRMEB 二开', '多诊所映射', '用户预约积分同步', '持续维护与日志排查'],
    links: [{ label: '访问项目', url: 'https://shop.maoju1991.com/' }],
    sections: [
      {
        title: '项目概述',
        items: [
          '基于 CRMEB 小程序做二次开发，目标是打通患者、预约、积分等核心数据。',
          '重点不是单个接口，而是多系统之间稳定运行的数据同步链路。',
          '难点集中在多诊所映射、老患者识别、预约重复写入和异常补偿。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '重构用户、预约、积分三条同步链路，补齐依赖检查和异常补偿。',
          '增加门店优先匹配、多患者待选、默认医生自动创建等业务逻辑。',
          '建设同步日志、监控报表、后台总览和手动同步能力。',
          '项目交付后持续跟进线上问题，通过看日志、查链路和补小改动维持系统稳定运行。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '让系统从“能调用”提升到“能稳定运行、能排查、能维护，并能持续迭代”。',
          '技术栈覆盖 ThinkPHP、Vue、MySQL、Redis 与异步队列。',
          '这是一个完整的系统对接与数据同步项目案例。',
        ],
      },
    ],
  },
  {
    id: 'hospital-education-system',
    title: '医院教育管理 SaaS 系统',
    subtitle: '服务多家三甲医院的教育培训与考核管理平台',
    category: 'enterprise',
    categoryLabel: '企业系统',
    year: '2022.06 - 2025.01 / Vue 2&3 / Node.js',
    summary:
      '面向医院教育培训场景的大型 SaaS 系统，覆盖学员全生命周期、课程体系、考试评价和档案管理等业务流程。我主要负责前端架构、核心模块交付与团队协作规范建设。',
    positioning:
      '这是典型的复杂后台业务系统，不只是做页面开发，而是围绕多租户、权限、动态表单和工程化能力建设，支撑长期迭代交付。',
    tags: ['Vue 2', 'Vue 3', 'TypeScript', 'Element UI', 'Node.js', 'Express', 'MySQL'],
    highlights: ['动态表单引擎', '多租户权限', '性能优化', '前端规范建设'],
    links: [],
    sections: [
      {
        title: '项目概述',
        items: [
          '系统服务多家三甲医院，覆盖学员、课程、考试评价、档案等完整流程。',
          '需要支撑多院区、多角色、多租户的数据隔离和权限控制。',
          '项目周期长、业务复杂度高，对架构稳定性和可维护性要求高。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '主导前端架构设计，建立基于 Vue2 / Vue3 的组件化开发体系。',
          '设计并实现 JSON 配置驱动的动态表单引擎，提高复杂表单开发效率。',
          '开发 Node.js 联调工具和前端监控能力，改善开发与排障体验。',
          '参与技术评审和新人培养，推动团队前端协作规范落地。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '页面加载速度提升约 30%，前端开发效率明显提升。',
          '动态表单能力可复用到其他项目，节省大量重复开发成本。',
          '在复杂医院业务场景下兼顾了功能交付、稳定性与团队协作。',
        ],
      },
    ],
  },
  {
    id: 'construction-project-system',
    title: '建筑装修项目管理系统',
    subtitle: 'PC 管理端与移动端一体化的工程项目全流程管理系统',
    category: 'enterprise',
    categoryLabel: '企业系统',
    year: '2021.09 - 2022.05 / Vue 3 / UniApp',
    summary:
      '为建筑装修行业打造的项目管理系统，覆盖立项、任务计划、现场执行与验收交付。项目由我独立完成全栈设计与开发，同时交付 PC 管理端和移动端应用。',
    positioning:
      '这个项目体现的重点是独立全栈交付能力，包括系统架构、数据库设计、接口、前端页面、移动端能力和业务组件建设。',
    tags: ['Vue 3', 'TypeScript', 'Ant Design', 'UniApp', 'uView', 'Node.js', 'MySQL'],
    highlights: ['独立全栈交付', 'Excel 批量导入', '甘特图组件', '移动端离线同步'],
    links: [],
    sections: [
      {
        title: '项目概述',
        items: [
          '项目覆盖工程项目从立项到竣工验收的完整流程。',
          '既有 PC 后台，也有现场移动端，要求跨端数据保持同步。',
          '需要处理大量任务关系、计划依赖和批量导入场景。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '独立完成数据库设计、API 规划、后台管理端与移动端开发。',
          '实现复杂 Excel 批量导入，支持多层任务结构识别与解析。',
          '开发甘特图交互组件，支持拖拽调整和实时进度同步。',
          '通过本地缓存和同步机制保证移动端现场作业连续性。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '移动端使用后提升了现场作业效率，减少沟通成本。',
          '复杂项目数据导入和计划管理能力成为系统亮点。',
          '很好体现了从 0 到 1 的独立交付和复杂交互实现能力。',
        ],
      },
    ],
  },
  {
    id: 'trading-platform',
    title: '数字货币交易平台后台管理系统',
    subtitle: '面向运营团队的大型交易平台后台与数据管理系统',
    category: 'enterprise',
    categoryLabel: '企业系统',
    year: '2019.10 - 2021.06 / Vue 2 / ECharts',
    summary:
      '交易平台后台系统面向 3 至 4 万注册用户和 100+ 内部运营人员，覆盖用户生命周期、权限控制、活动运营和理财产品管理等核心模块。',
    positioning:
      '项目重点在于高并发平台下的后台治理能力，包括权限体系、数据可视化、监控预警和复杂业务模块的工程化组织。',
    tags: ['Vue 2', 'Element UI', 'ECharts', 'Node.js', 'Express', 'MySQL', 'Redis'],
    highlights: ['运营后台', '数据可视化', '监控预警'],
    links: [],
    sections: [
      {
        title: '项目概述',
        items: [
          '系统承接用户、认证、风控、营销、理财等运营后台能力。',
          '要求在复杂权限和高并发背景下保持稳定性与可维护性。',
          '需要实时展示关键业务指标，支撑管理决策。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '设计多角色权限管理结构，支撑复杂后台权限组合。',
          '参与用户管理、营销活动、理财产品等核心模块开发。',
          '使用 ECharts 构建数据看板，提升运营数据可视化能力。',
          '建立系统监控与预警机制，并持续做性能优化。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '页面加载与接口响应性能得到明显改善。',
          '权限系统和可视化能力支撑了复杂运营场景。',
          '体现了金融类复杂后台系统的稳定性建设经验。',
        ],
      },
    ],
  },
  {
    id: 'medical-beauty-website',
    title: '医疗美容官网与商品展示系统',
    subtitle: '面向医疗美容机构的官网展示与内容管理项目',
    category: 'web',
    categoryLabel: '网站项目',
    year: '2018.05 - 2019.08 / Vue / ThinkPHP',
    summary:
      '为医疗美容机构独立完成官网和商品展示系统开发，兼顾品牌展示、商品信息管理、内容维护和合规要求，是职业早期的重要独立项目。',
    positioning:
      '这个项目的核心不是炫技，而是在行业规范约束下把展示、管理和合规要求平衡起来，形成完整可用的网站方案。',
    tags: ['JavaScript', 'Vue', 'HTML/CSS', 'ThinkPHP', 'MySQL'],
    highlights: ['独立交付', '响应式官网', '内容管理后台', '行业合规'],
    links: [],
    sections: [
      {
        title: '项目概述',
        items: [
          '项目包含医院官网与商品展示系统两部分，服务品牌展示与业务介绍。',
          '需要适配多端展示，并兼顾医疗行业内容规范。',
          '是一个完整的独立交付型 Web 项目。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '独立完成官网页面设计与前端开发，实现响应式布局和交互效果。',
          '实现商品分类、筛选、详情展示等商品内容模块。',
          '基于 ThinkPHP 开发内容管理后台，支持内容维护和管理。',
          '梳理合规边界，保证站点展示内容符合行业要求。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '顺利交付完整官网与展示系统，获得客户认可。',
          '积累了网站建设、后台管理与独立项目推进经验。',
          '是职业早期很能体现执行力与责任感的案例。',
        ],
      },
    ],
  },
  {
    id: 'personal-website',
    title: '个人网站项目',
    subtitle: '基于 Next.js 的个人展示网站与作品整理平台',
    category: 'web',
    categoryLabel: '网站项目',
    year: '2024 - 至今 / Next.js / TypeScript',
    summary:
      '这个项目是我用来整理个人介绍、项目经验和博客内容的展示网站，采用 Next.js、React、TypeScript 与 CSS Modules 构建，持续迭代中。',
    positioning:
      '它既是个人品牌展示工具，也是我整理项目表达方式、沉淀内容结构和验证前端体验设计的长期实验项目。',
    tags: ['Next.js', 'React', 'TypeScript', 'Framer Motion', 'CSS Modules'],
    highlights: ['响应式设计', '主题切换', '动画体验', '项目与博客整合'],
    links: [],
    sections: [
      {
        title: '项目概述',
        items: [
          '网站用于展示个人介绍、真实项目案例和博客文章。',
          '采用现代前端技术栈，兼顾页面体验与结构清晰度。',
          '项目会随着内容沉淀持续调整和完善。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '完成整体信息架构、页面布局和前端实现。',
          '集成主题切换、动效体验和项目内容展示模块。',
          '持续优化作品表达，让项目介绍更贴近真实业务能力。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '形成了一个可持续更新的个人作品展示平台。',
          '既能对外展示能力，也能作为内容组织与表达的实验场。',
          '这次合并后，旧版项目与个人介绍内容也被纳入当前版本中。',
        ],
      },
    ],
  },
];

export const featuredProjectCaseStudies = projectCaseStudies.slice(0, 3);
