export const navLinks = [
  { to: '/', label: '首页' },
  { to: '/about', label: '关于我' },
  { to: '/skills', label: '技能' },
  { to: '/projects', label: '项目' },
  { to: '/contact', label: '联系方式' }
];

export type ProjectItem = {
  slug: string;
  name: string;
  summary: string;
  type: '网站' | '应用' | '开源' | '设计';
  stack: string;
  date: string;
  role: string;
  duration: string;
  status: '已完成' | '进行中' | '维护中';
  challenge: string;
  solution: string;
  tradeoff: string;
  retrospective: string;
  impact: string;
  metrics: string[];
  overview: string[];
  architecture: string[];
  links: {
    demo?: string;
    repo?: string;
    doc?: string;
  };
};

export const coreSkills = [
  { name: 'React + TypeScript', level: '4/5', desc: '组件化开发与状态管理' },
  { name: 'CSS / Tailwind', level: '4/5', desc: '响应式布局与设计系统' },
  { name: 'Node.js API', level: '3/5', desc: 'REST API 与服务集成' },
  { name: '工程化与部署', level: '4/5', desc: 'CI/CD 与性能优化' }
];

export const featuredProjects: ProjectItem[] = [
  {
    slug: 'personal-website-v1',
    name: 'Personal Website V1',
    summary: '基于 React + TypeScript 的个人展示站，聚焦内容表达与可维护性。',
    type: '网站',
    stack: 'React',
    date: '2026-03-01',
    role: '独立开发',
    duration: '3 周',
    status: '进行中',
    challenge: '如何在静态部署前提下兼顾内容展示、交互与后续扩展。',
    solution:
      '采用 V1/V2/V3 分层方案，V1 先交付静态能力，动态功能使用托管服务解耦。',
    tradeoff: '牺牲部分“自建可控性”，换取上线速度与维护成本可控。',
    retrospective: '后续应进一步将内容数据结构化，减少页面硬编码成本。',
    impact: '建立可持续迭代的个人站点基础，降低后续改版成本。',
    metrics: [
      '首批页面覆盖 5 个核心模块',
      '计划任务可追踪率提升到 100%',
      '发布链路从手动变为自动化'
    ],
    overview: [
      '该项目用于搭建个人品牌展示基础，明确 V1/V2/V3 范围，降低执行过程中的范围蔓延风险。',
      '工程上采用 React + TypeScript + Vite，优先构建可维护结构和可复用组件，再逐步细化内容。',
      '部署层面以 GitHub Pages + Actions 为主，确保持续交付能力。'
    ],
    architecture: ['页面层：路由与页面组件', '组件层：Navbar/Footer/Card/Form 等可复用组件', '数据层：静态数据配置与任务文档联动'],
    links: {
      demo: '#',
      repo: '#',
      doc: '#'
    }
  },
  {
    slug: 'monitoring-dashboard',
    name: 'Monitoring Dashboard',
    summary: '自动化监控与告警展示面板，支持多任务状态追踪。',
    type: '应用',
    stack: 'TypeScript',
    date: '2025-11-18',
    role: '前端负责人',
    duration: '6 周',
    status: '已完成',
    challenge: '多数据源状态更新频繁，页面渲染与交互容易卡顿。',
    solution: '引入分层状态管理与虚拟化展示，拆分高频刷新区域。',
    tradeoff: '初期代码复杂度提升，但换来稳定的交互性能。',
    retrospective: '应更早引入性能预算和监控埋点，减少后期排障时间。',
    impact: '告警处理效率提升，监控页面交互延迟显著降低。',
    metrics: ['告警处理平均时长下降 30%', '关键视图渲染耗时下降 40%'],
    overview: [
      '该项目聚焦多来源状态监控，核心目标是让运维和研发快速定位异常。',
      '通过数据分层、渲染优化和 UI 信息层级重构，提高了可读性和响应速度。'
    ],
    architecture: ['采集层：多来源状态拉取', '处理层：统一数据模型与告警规则', '展示层：仪表盘可视化与交互筛选'],
    links: {
      demo: '#',
      repo: '#'
    }
  },
  {
    slug: 'docs-workflow-tooling',
    name: 'Docs Workflow Tooling',
    summary: '文档模板与任务流程联动，提升团队执行效率。',
    type: '开源',
    stack: 'Node.js',
    date: '2025-09-08',
    role: '架构与开发',
    duration: '4 周',
    status: '维护中',
    challenge: '文档与执行状态脱节，任务追踪成本高。',
    solution: '统一模板、增加检查脚本、联动任务状态输出。',
    tradeoff: '需要团队在初期投入规范迁移成本。',
    retrospective: '模板规范应配合 CI 校验，减少人工检查。',
    impact: '降低文档维护成本，提高协作透明度。',
    metrics: ['文档结构一致性提升', '任务追踪时间明显降低'],
    overview: [
      '项目目标是把文档从“记录工具”升级为“执行工具”，让状态与计划同步。',
      '通过模板化与脚本化联动，减少信息散落和重复维护。'
    ],
    architecture: ['模板层：标准文档结构', '脚本层：检查与状态同步脚本', '协作层：任务看板与审阅流程'],
    links: {
      repo: '#',
      doc: '#'
    }
  }
];

export const aboutTimeline = [
  { year: '2021', title: '工程基础建设', detail: '系统学习前端与计算机基础，形成工程化意识。' },
  {
    year: '2023',
    title: '项目交付阶段',
    detail: '参与多个实际项目，积累需求拆解、开发与发布经验。'
  },
  {
    year: '2025',
    title: '效率与质量优化',
    detail: '聚焦自动化流程、CI/CD 与前端性能优化实践。'
  },
  {
    year: '2026',
    title: '个人品牌站建设',
    detail: '建立个人网站体系，形成可持续的内容与作品输出。'
  }
];

export const valuePrinciples = [
  {
    name: '边界先行',
    example: '在开发前先明确 V1/V2 范围，避免需求扩散影响交付。'
  },
  {
    name: '交付优先',
    example: '先实现可用版本，再通过小步迭代提升性能与体验。'
  },
  {
    name: '证据驱动',
    example: '技能与成果都绑定项目案例或量化指标。'
  }
];

export const skillMatrix = [
  {
    group: '前端开发',
    items: [
      {
        name: 'React + TypeScript',
        level: '4/5',
        recent: '2026-Q1',
        evidence: 'Personal Website V1 路由与组件体系'
      },
      {
        name: '响应式布局',
        level: '4/5',
        recent: '2026-Q1',
        evidence: 'Navbar 移动菜单与多断点布局'
      },
      {
        name: 'Tailwind / Design Token',
        level: '4/5',
        recent: '2026-Q1',
        evidence: '统一颜色变量与组件样式规范'
      }
    ]
  },
  {
    group: '后端与工程化',
    items: [
      {
        name: 'Node.js 服务集成',
        level: '3/5',
        recent: '2025-Q4',
        evidence: '监控看板数据接口整合'
      },
      {
        name: 'CI/CD 发布',
        level: '4/5',
        recent: '2026-Q1',
        evidence: 'GitHub Actions + Pages 自动发布流程'
      },
      {
        name: '性能与可访问性',
        level: '4/5',
        recent: '2026-Q1',
        evidence: 'DoD 中包含 Lighthouse 指标门槛'
      }
    ]
  }
];

export const backendSkillDetails = [
  'API 设计：REST 结构、状态码规范、统一响应格式。',
  '鉴权实践：基于 Token 的会话校验流程设计。',
  '数据库经验：关系与文档模型的基础使用和查询优化思路。',
  '部署实践：前后端分层发布、环境变量与配置管理。'
];

export const engineeringSkillDetails = [
  'Git 流程：分支策略、PR 评审、变更记录。',
  'CI/CD：GitHub Actions 自动化构建发布。',
  '云与托管：GitHub Pages、静态部署策略。',
  '性能与安全：Lighthouse 指标、最小化采集与隐私边界。'
];

export const softSkillCases = [
  {
    title: '项目管理',
    case: '按周拆解目标与风险项，确保每周有可验收产出。'
  },
  {
    title: '团队协作',
    case: '通过任务清单和文档同步，减少口头沟通造成的信息偏差。'
  },
  {
    title: '沟通表达',
    case: '将技术方案拆解为可执行步骤，便于非技术角色理解进度。'
  },
  {
    title: '问题解决',
    case: '先定位边界条件，再分层排查，避免盲目试错。'
  }
];
