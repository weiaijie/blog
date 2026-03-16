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
] as const;

export const projectCaseStudies: ProjectCaseStudy[] = [
  {
    id: 'maoju-dental-sync',
    title: '茂菊口腔项目案例分析',
    subtitle: '连锁口腔诊所业务系统与小程序数据打通案例',
    category: 'integration',
    categoryLabel: '系统对接',
    year: 'ThinkPHP 6 / CRMEB / 数据同步',
    summary:
      '围绕茂菊口腔小程序与轻松牙医系统之间的数据流，搭建一套可持续运行的数据同步体系，覆盖用户同步、预约同步、积分同步、默认医生创建、异常修复、定时任务和后台管理。',
    positioning:
      '这个项目不是单纯开发接口，而是把诊所侧患者、预约、积分数据与小程序侧用户、订单稳定联动起来，最终形成可持续运行、可排查、可维护的数据同步中台。',
    tags: ['PHP 7.4', 'ThinkPHP 6', 'Vue 2', 'MySQL', 'Redis', 'CRMEB', '队列异步'],
    highlights: [
      '多诊所、多数据库、多表后缀的动态映射',
      '用户、预约、积分三条核心同步链路',
      '幂等校验、异常补偿与日志追踪',
      '同步后台总览、手动同步与排障能力',
    ],
    links: [{ label: '访问项目', url: 'https://shop.maoju1991.com/' }],
    sections: [
      {
        title: '项目概述',
        items: [
          '对接 CRMEB 小程序后台与轻松牙医、青松牙医系统，目标是打通患者、预约、积分等核心数据。',
          '项目重点不是单个接口开发，而是把多系统之间的数据同步做成可持续运行的业务链路。',
          '难点集中在多诊所映射、老患者识别、预约重复写入和线上异常补偿。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '重构用户、预约、积分三条同步链路，补齐依赖检查、异常补偿和幂等控制。',
          '增加门店优先匹配、多患者待选、默认医生自动创建等关键业务逻辑。',
          '建设同步日志、监控表、后台总览和手动同步能力，方便排查和运维。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '技术栈为 PHP 7.4、ThinkPHP 6、Vue 2、MySQL、Redis，并通过队列任务做异步同步。',
          '最终让这套对接链路从“能调用”提升到“能稳定运行、能排查、能维护”。',
          '这是一个适合放在作品集里的系统对接与数据同步代表案例。',
        ],
      },
    ],
  },
  {
    id: 'ebmpapst-mini-program',
    title: '依必安派特大中华区小程序项目案例分析',
    subtitle: '企业级会员运营与内容服务一体化微信小程序',
    category: 'mini-program',
    categoryLabel: '微信小程序',
    year: 'uni-app / Vue 3 / 企业服务',
    summary:
      '面向企业会员、经销商和潜在客户的微信小程序项目，融合会员运营、内容分发、活动管理、业务申请、销售支持与 AI 导览能力，形成完整的企业私域服务闭环。',
    positioning:
      '这个项目不是单一品牌展示型小程序，而是把品牌内容、用户身份体系、积分激励、活动报名、资料中心和业务咨询统一收拢到一个移动端触点中。',
    tags: ['uni-app', 'Vue 3', 'Vite', 'uview-plus', 'SCSS', '微信登录', '动态表单'],
    highlights: [
      '会员中心、内容中心、活动中心一体化',
      '分包架构与统一请求层封装',
      '权限标签驱动的角色化功能开放',
      '动态表单、内容检索与 AI 导览式问答',
    ],
    links: [{ label: '查看后台', url: 'https://yibiante.test.weiseo.com/' }],
    sections: [
      {
        title: '项目概述',
        items: [
          '这是一个面向会员、经销商和潜在客户的企业服务型微信小程序，不是单纯品牌展示页。',
          '项目把会员中心、内容中心、活动报名、业务申请和 AI 导览整合到一个微信入口中。',
          '更适合包装成企业级会员运营与内容服务一体化小程序，当前对外提供后台测试地址，小程序前台不单独开放 H5。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '基于 uni-app + Vue 3 + Vite 开发，采用分包架构和统一请求层封装。',
          '梳理首页导航、会员中心、活动报名、资料中心、业务表单和 AI 小助理等核心模块。',
          '通过权限标签、静默登录、动态表单和内容检索能力，支撑持续运营场景。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '核心价值是把内容触达、活动运营、商机收集和用户沉淀放到一个统一入口里。',
          '项目亮点包括分包架构、权限标签控制、动态表单和 AI 导览式问答。',
          '这是一个适合官网展示的企业微信小程序案例，但建议配 2 到 4 张页面截图一起展示。',
        ],
      },
    ],
  },
  {
    id: 'xiangyi-benefit-mall',
    title: '香溢金联企业福利商城与供应商分账项目案例分析',
    subtitle: '企业福利商城与供应商结算一体化改造项目',
    category: 'commerce',
    categoryLabel: '电商改造',
    year: 'CRMEB PRO / ThinkPHP 8 / 支付结算',
    summary:
      '围绕企业客户采购、员工福利消费、供应商结算、组合支付和平台管理展开，完成企业福利场景下的商城核心业务改造与支付结算链路设计。',
    positioning:
      '这个项目不是普通商城二开，而是把企业后台、员工端、平台端和供应商端打通，形成可落地、可运营、可对账的企业福利业务系统。',
    tags: ['CRMEB PRO', 'ThinkPHP 8', 'MySQL', 'Redis', 'Swoole', '组合支付', '供应商分账'],
    highlights: [
      '企业客户体系与员工福利金能力搭建',
      '福利金、余额、在线支付组合支付链路',
      '供应商分账、平台补贴与退款流水一致性',
      '复用现有商城能力完成大幅业务扩展',
    ],
    links: [
      { label: '访问测试环境', url: 'https://test.wx.sunnycloudtop.com/' },
      { label: '访问正式地址', url: 'https://wx.sunnycloudtop.com/' },
    ],
    sections: [
      {
        title: '项目概述',
        items: [
          '这是一个企业福利商城改造项目，不是普通商城二开。',
          '核心场景包括企业客户采购、员工福利消费、组合支付和供应商结算。',
          '难点集中在多角色权限、资金流转、分账逻辑和退款回滚一致性。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '搭建企业客户、员工福利金和商品企业权限体系，让企业身份真正进入交易链路。',
          '重构组合支付流程，把立即扣款改成延迟确认，降低支付失败后的资金风险。',
          '重做供应商分账、平台补贴和退款流水逻辑，保证账务和状态一致。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '技术基于 CRMEB PRO、ThinkPHP 8、MySQL、Redis、Swoole，在现有商城能力上做结构化扩展。',
          '项目亮点是组合支付、供应商分账和退款回滚的一致性设计。',
          '这是一个更偏复杂业务系统与交易链路设计的案例，适合配后台流程或支付结算截图。',
        ],
      },
    ],
  },
  {
    id: 'ebmpapst-admin-console',
    title: '依必安特后台管理系统案例',
    subtitle: '企业内容运营、活动配置与业务表单管理后台',
    category: 'integration',
    categoryLabel: '后台系统',
    year: 'Vue / 内容运营 / 配置后台',
    summary:
      '这是依必安特小程序配套的后台系统，主要承担内容管理、活动配置、业务表单处理、权限控制和数据运营支撑，是前台小程序持续运营的核心中台。',
    positioning:
      '这个案例的重点不在单个后台页面，而在如何让内容、活动、表单和用户权限通过后台形成持续可运营、可配置、可排查的业务闭环。',
    tags: ['后台系统', '运营配置', '权限控制', '内容管理', '表单管理'],
    highlights: [
      '支撑小程序端的内容、活动和业务配置',
      '后台配置驱动前台页面和表单展示',
      '权限控制与运营流程协同',
      '适合作为企业运营后台案例展示',
    ],
    links: [{ label: '查看后台', url: 'https://yibiante.test.weiseo.com/' }],
    sections: [
      {
        title: '项目概述',
        items: [
          '这是依必安特小程序的配套后台，不直接面向终端用户，而是面向运营、内容和业务管理人员。',
          '后台承接了内容发布、活动配置、资料管理、业务表单处理和权限控制等核心工作。',
          '它的作用是让前台小程序从静态展示工具变成可持续运营的平台。',
        ],
      },
      {
        title: '我的工作',
        items: [
          '围绕内容中心、活动中心、表单中心和权限控制梳理后台支撑能力。',
          '让前台的活动报名、资料中心、业务申请等功能可以由后台做配置和维护。',
          '把后台能力和前台小程序联动起来，提升后续运营和维护效率。',
        ],
      },
      {
        title: '结果与亮点',
        items: [
          '后台不是简单的增删改查页面，而是小程序运营体系里的业务中台。',
          '核心亮点是配置驱动、权限控制和前后台联动，而不是单一视觉效果。',
          '如果后续补上 2 到 3 张后台截图，这个案例会比只写文字更有说服力。',
        ],
      },
    ],
  },
];

export const featuredProjectCaseStudies = projectCaseStudies.slice(0, 3);
