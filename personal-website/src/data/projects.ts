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
    subtitle: '在 CRMEB PRO 上改企业福利采购和分账流程',
    category: 'commerce',
    categoryLabel: '电商改造',
    year: '2025.11 - 2026.02.14 / CRMEB PRO / ThinkPHP 8',
    summary:
      '这个项目一开始不是从零写商城，而是在 CRMEB PRO 现有系统上继续改。客户要的是企业福利采购场景，所以原来的普通商城流程不太够用，需要补企业用户、员工福利金、供应商结算、支付和退款这些业务。',
    positioning:
      '我这边主要负责配合业务把流程跑通，包括企业用户管理后台、后台前端、小程序端页面，以及支付分账相关调整。项目上线后还在持续维护，后面有问题和业务变动也会继续处理。',
    tags: ['CRMEB PRO', 'ThinkPHP 8', 'MySQL', 'Redis', 'Swoole', '组合支付', '供应商分账'],
    highlights: ['CRMEB PRO 二开', '企业用户后台', '支付和分账流程', '后台和小程序页面'],
    links: [
      { label: '访问测试环境', url: 'https://test.wx.sunnycloudtop.com/' },
      { label: '访问正式地址', url: 'https://wx.sunnycloudtop.com/' },
    ],
    sections: [
      {
        title: '当时的情况',
        items: [
          '客户原来用的是 CRMEB PRO，但企业福利采购和普通商城不太一样。',
          '要处理企业账号、员工福利金、商品权限、供应商结算和支付退款这些流程。',
          '上线之后也不是结束，后面还会继续改业务规则、处理线上问题。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '把原来的商城流程改成适合企业福利场景的业务流程。',
          '新增企业用户管理后台，并处理后台前端和小程序端相关页面和流程。',
          '梳理企业客户、员工福利金、商品权限这些业务规则。',
          '重新整理支付、分账、退款流程，尽量把对账异常风险往下压。',
          '上线后持续维护，处理线上问题和业务调整。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '最后这套流程能支撑企业福利采购，不再只是普通商城下单。',
          '后台和小程序之间的几个关键流程也打通了。',
          '这个项目后面还在维护，所以很多改动都会考虑后续好不好查、好不好继续改。',
        ],
      },
    ],
  },
  {
    id: 'ebmpapst-mini-program',
    title: '依必安派特大中华区小程序与后台管理系统',
    subtitle: '企业小程序和配套后台一起做的项目',
    category: 'mini-program',
    categoryLabel: '小程序 / 后台一体化',
    year: '2025.10 - 2025.11中旬 / uni-app / Vue 3 / Vue',
    summary:
      '这个项目是企业小程序加后台一起做。小程序面向会员、经销商和潜在客户，后台给运营人员维护内容、活动、资料、表单和权限，不是只做一个展示首页。',
    positioning:
      '我主要做前台小程序和配套后台功能，把会员中心、活动报名、资料中心、业务申请这些模块串起来。后面上线以后，也继续根据反馈修问题、补小需求。',
    tags: ['uni-app', 'Vue 3', 'Vite', 'uview-plus', 'Vue', '微信登录', '动态表单', '后台配置'],
    highlights: ['小程序页面', '会员中心', '活动和资料配置', '上线后维护'],
    links: [{ label: '查看后台', url: 'https://yibiante.test.weiseo.com/' }],
    sections: [
      {
        title: '当时的情况',
        items: [
          '客户需要的不只是一个企业介绍小程序，后台也要能让运营人员自己维护内容。',
          '小程序面向会员、经销商和潜在客户，后台负责内容、活动、表单和权限。',
          '很多页面看起来是展示，但背后都要和后台配置对应起来。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '负责小程序前台功能开发，同时做配套后台配置和管理功能。',
          '完成会员中心、活动报名、资料中心这些主要页面。',
          '实现后台内容发布、活动配置、表单处理和权限相关功能。',
          '上线后持续修问题、接反馈、补小需求。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '前台小程序和后台配置能配合使用，内容维护不用每次都找开发改代码。',
          '活动、资料和表单这些内容后面可以继续扩展。',
          '上线后根据反馈改过一些细节，也比较考验前后台一起看问题的能力。',
        ],
      },
    ],
  },
  {
    id: 'maoju-dental-sync',
    title: '茂菊口腔',
    subtitle: '把 CRMEB 小程序和诊所系统的数据接起来',
    category: 'integration',
    categoryLabel: '系统对接',
    year: '2025.08 - 2025.09 / ThinkPHP 6 / CRMEB',
    summary:
      '茂菊口腔这个项目是在 CRMEB 小程序体系上继续改。主要麻烦点在于，小程序这边的数据要和轻松牙医系统同步，用户、预约、积分这些数据不能只靠人工处理。',
    positioning:
      '我负责把同步流程做起来，也补了门店匹配、默认医生、多患者选择、日志和后台手动同步这些细节。这个项目后续也需要维护，所以我比较重视出问题时能不能查得到。',
    tags: ['PHP 7.4', 'ThinkPHP 6', 'Vue 2', 'MySQL', 'Redis', 'CRMEB', '异步队列'],
    highlights: ['CRMEB 二开', '诊所映射', '预约和积分同步', '日志和手动同步'],
    links: [{ label: '访问项目', url: 'https://shop.maoju1991.com/' }],
    sections: [
      {
        title: '当时的情况',
        items: [
          '这个项目是在已有 CRMEB 小程序上继续改，不是重做一套。',
          '难点在于小程序和轻松牙医系统里的用户、预约、积分要能对上。',
          '同步出错以后也要能查，所以日志和后台处理入口很重要。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '负责用户、预约、积分三条同步逻辑。',
          '补齐门店匹配、默认医生创建、多患者选择这些业务细节。',
          '增加日志、后台查看和手动同步功能，方便排查和处理问题。',
          '交付后继续维护，通过日志定位问题并处理小需求。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '用户、预约和积分这些同步流程基本跑顺了。',
          '出问题时可以通过日志和后台信息更快定位。',
          '这类项目让我更注意“上线后怎么查问题”，而不是只把接口调通。',
        ],
      },
    ],
  },
  {
    id: 'aomori-travel-map-php-upgrade',
    title: '青森旅地图',
    subtitle: '把一个老 PHP 公共交通网站迁到 PHP 8.2',
    category: 'web',
    categoryLabel: '网站项目',
    year: 'PHP 5.6/7 -> 8.2 / 多语言公共交通门户',
    summary:
      '青森旅地图是一个已经在线运行很久的公共交通门户，里面有铁路、巴士、轮渡路线和观光信息，也有多语言内容。这次主要不是加新功能，而是把老 PHP 环境升级上去。',
    positioning:
      '我做的重点是把 PHP 5.6 / 7 相关的兼容问题处理掉，让站点能迁到 PHP 8.2。老项目升级最怕线上出问题，所以迁移、回归和环境适配都要比较谨慎。',
    tags: ['PHP 8.2', 'PHP 升级', '兼容性迁移', '多语言网站', '运行环境适配', '低停服升级'],
    highlights: ['PHP 版本升级', '兼容问题修复', '环境适配', '迁移前后测试'],
    links: [{ label: '访问网站', url: 'https://aomoritravelmap.com/jp/' }],
    sections: [
      {
        title: '当时的情况',
        items: [
          '这是一个已经在线运行多年的公共交通网站。',
          '站点里有铁路、巴士、轮渡路线、观光信息，也有多语言内容。',
          '这次主要是升级 PHP 版本，尽量别影响线上访问。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '负责旧版 PHP 环境迁移到 PHP 8.2，并梳理升级过程里的兼容风险。',
          '处理废弃函数、类型声明、扩展变更这些常见兼容问题。',
          '适配运行环境和依赖，让站点能在 PHP 8.2 下正常跑起来。',
          '配合迁移和回归测试，尽量把停服时间压低。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '老站最后迁到了 PHP 8.2。',
          '主要页面和多语言内容在升级后还能正常访问。',
          '这种项目没有太多“炫技”的地方，关键是少出问题、能平稳切过去。',
        ],
      },
    ],
  },
  {
    id: 'hospital-education-system',
    title: '医院教育管理 SaaS 系统',
    subtitle: '医院培训、考试和档案相关的后台系统',
    category: 'enterprise',
    categoryLabel: '企业系统',
    year: '2022.06 - 2025.01 / Vue 2&3 / Node.js',
    summary:
      '这个系统做的是医院里的教育培训管理，使用方包括多家三甲医院。里面有学员档案、课程、考试、评价、轮转和各种后台配置，业务线比较长。',
    positioning:
      '我在里面主要做前端架构、复杂页面、动态表单和一些联调工具。这个项目做的时间比较久，也让我更熟悉复杂后台长期迭代时要怎么控制组件、权限、性能和协作成本。',
    tags: ['Vue 2', 'Vue 3', 'TypeScript', 'Element UI', 'Node.js', 'Express', 'MySQL'],
    highlights: ['动态表单', '权限和租户', '页面性能', '前端协作规范'],
    links: [],
    sections: [
      {
        title: '当时的情况',
        items: [
          '这是一个给医院教育培训使用的 SaaS 系统。',
          '业务上有学员档案、课程、考试、评价、轮转和档案管理这些流程，服务过多家三甲医院。',
          '系统模块多、周期长，很多能力都要考虑后续继续迭代。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '参与前端架构和组件拆分，项目里同时用到 Vue2 和 Vue3。',
          '做过 JSON 配置驱动的动态表单，减少一些重复表单开发。',
          '写过 Node.js 联调工具，也处理过前端监控和排查问题相关的工作。',
          '参与代码评审和新人带教，把一些常见写法和协作规则固定下来。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '一些页面加载和表单开发效率有明显改善。',
          '动态表单后面也能复用到类似模块里。',
          '这个项目周期比较长，让我对复杂后台的维护成本更敏感。',
        ],
      },
    ],
  },
  {
    id: 'construction-project-system',
    title: '建筑装修项目管理系统',
    subtitle: 'PC 管理端和移动端一起做的工程管理系统',
    category: 'enterprise',
    categoryLabel: '企业系统',
    year: '2021.09 - 2022.05 / Vue 3 / UniApp',
    summary:
      '这个项目是给建筑装修行业做的项目管理系统，PC 管理端和移动端都要有。业务从立项、任务计划，到现场执行、进度反馈和验收交付都有涉及。',
    positioning:
      '这套系统基本是我独立推进的，从数据库、接口、后台页面到移动端都一起做。印象比较深的是 Excel 批量导入、甘特图和移动端现场使用这些细节，做起来比普通后台页面更费脑子。',
    tags: ['Vue 3', 'TypeScript', 'Ant Design', 'UniApp', 'uView', 'Node.js', 'MySQL'],
    highlights: ['独立完成主要功能', 'Excel 批量导入', '甘特图', '移动端离线缓存'],
    links: [],
    sections: [
      {
        title: '当时的情况',
        items: [
          '这是给建筑装修行业做的项目管理系统。',
          '业务包括立项、任务计划、现场执行、进度反馈和验收。',
          'PC 管理端和移动端都要做，很多功能要考虑现场使用习惯。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '独立完成数据库设计、接口规划、后台管理端和移动端开发。',
          '实现复杂 Excel 批量导入，支持多层任务结构识别和解析。',
          '开发甘特图交互组件，支持拖拽调整和实时进度同步。',
          '给移动端加了本地缓存和同步处理，避免现场网络不好时完全没法用。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '现场记录和项目计划能放到系统里统一处理。',
          'Excel 导入和甘特图是当时花时间比较多的部分。',
          '这段经历对我来说比较重要，因为很多东西都要自己从头想清楚。',
        ],
      },
    ],
  },
  {
    id: 'trading-platform',
    title: '数字货币交易平台后台管理系统',
    subtitle: '交易平台内部运营使用的后台系统',
    category: 'enterprise',
    categoryLabel: '企业系统',
    year: '2019.10 - 2021.06 / Vue 2 / ECharts',
    summary:
      '这个后台服务的是一个交易平台，注册用户大概三四万，内部运营人员也不少。后台里有用户管理、权限、活动、理财产品、数据看板和一些运营流程。',
    positioning:
      '我参与了多个后台模块，也做过权限、图表和监控相关内容。这个阶段更多是在复杂后台里打磨稳定性和可维护性，不能只把页面做出来，还要让运营每天能用。',
    tags: ['Vue 2', 'Element UI', 'ECharts', 'Node.js', 'Express', 'MySQL', 'Redis'],
    highlights: ['运营后台', '权限模块', '数据图表', '监控预警'],
    links: [],
    sections: [
      {
        title: '当时的情况',
        items: [
          '这是交易平台内部运营使用的后台系统。',
          '当时注册用户大概三四万，后台使用人员也不少。',
          '里面有用户、权限、活动、理财产品和数据看板等模块。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '参与多角色权限管理、用户管理、营销活动和理财产品等模块。',
          '用 ECharts 做过后台数据看板。',
          '参与监控和预警相关功能，也处理过一些性能问题。',
          '日常更多是在已有后台里持续改模块、修问题。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '后台能支撑运营人员日常处理用户、活动和产品相关工作。',
          '权限和数据看板是比较常用的部分。',
          '这个阶段让我更熟悉运营后台里那些长期维护的小问题。',
        ],
      },
    ],
  },
  {
    id: 'medical-beauty-website',
    title: '医疗美容官网与商品展示系统',
    subtitle: '早期独立做的官网和商品展示后台',
    category: 'web',
    categoryLabel: '网站项目',
    year: '2018.05 - 2019.08 / Vue / ThinkPHP',
    summary:
      '这是我比较早期独立做的项目，给医疗美容机构做官网和商品展示。那时候项目没有现在这么复杂，但从页面、内容管理到上线，都需要自己一点点推进。',
    positioning:
      '我主要负责官网页面、响应式效果、商品展示和 ThinkPHP 后台。医疗美容行业对展示内容有要求，所以除了做功能，也要注意内容管理和合规边界。',
    tags: ['JavaScript', 'Vue', 'HTML/CSS', 'ThinkPHP', 'MySQL'],
    highlights: ['独立开发', '响应式页面', '内容后台', '展示内容管理'],
    links: [],
    sections: [
      {
        title: '当时的情况',
        items: [
          '这是我比较早期独立完成的一个项目。',
          '主要是给医疗美容机构做官网和商品展示系统。',
          '当时更重要的是把展示、后台维护和行业要求一起考虑进去。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '独立完成官网页面和前端开发，做了响应式布局和基础交互。',
          '实现商品分类、筛选、详情展示这些商品内容模块。',
          '基于 ThinkPHP 开发内容管理后台，支持内容维护和管理。',
          '梳理合规边界，保证站点展示内容符合行业要求。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '网站和后台最后正常上线使用。',
          '这个项目让我比较早接触到从页面到后台再到上线的完整流程。',
          '现在回头看不算复杂，但对当时的我来说很锻炼。',
        ],
      },
    ],
  },
  {
    id: 'personal-website',
    title: '个人网站项目',
    subtitle: '用来整理个人介绍和项目经历的网站',
    category: 'web',
    categoryLabel: '网站项目',
    year: '2025 - 至今 / Next.js / TypeScript',
    summary:
      '这个个人网站就是现在这个站。最开始是想把个人介绍、项目经历和一些笔记整理出来，后面慢慢发现，真正难的不是写代码，而是怎么把做过的事情讲清楚。',
    positioning:
      '我用 Next.js、React、TypeScript 和 CSS Modules 做这一版，也会持续调整页面、文案和部署流程。它既是对外展示，也是我自己练习表达和整理项目的地方。',
    tags: ['Next.js', 'React', 'TypeScript', 'Framer Motion', 'CSS Modules'],
    highlights: ['项目整理', '响应式页面', '主题切换', '静态部署'],
    links: [],
    sections: [
      {
        title: '当时的情况',
        items: [
          '这个站主要用来整理个人介绍、项目经验和博客内容。',
          '整体用 Next.js、React、TypeScript 和 CSS Modules 来做，现在也还在持续迭代。',
          '现在也在不断调整文案，因为项目经历怎么写清楚其实挺难。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '完成页面结构、布局和前端实现。',
          '做了主题切换、简单动效、项目和博客内容展示。',
          '持续调整项目文案，尽量少一点包装，多一点真实细节。',
        ],
      },
      {
        title: '后来怎样',
        items: [
          '现在这个站已经能作为个人项目展示使用。',
          '后面还会继续补项目细节和博客内容。',
          '旧版项目里的内容也会慢慢迁到现在这一版。',
        ],
      },
    ],
  },
];
