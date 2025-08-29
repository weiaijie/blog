/**
 * skills.ts
 *
 * 描述：技能数据配置文件，定义技能分类、熟练度和相关信息
 *
 * 功能：
 * - 定义技能分类和层级结构
 * - 提供技能熟练度评级系统
 * - 包含技能描述和相关项目经验
 *
 * 主要接口/常量：
 * - SkillItem：技能项目接口
 * - SkillCategory：技能分类接口
 * - skillsData：技能数据
 *
 * 导出：
 * - 技能相关的类型定义和数据
 */

// 技能熟练度等级
export type SkillLevel = 1 | 2 | 3 | 4 | 5;

// 技能项目接口
export interface SkillItem {
  id: string;
  name: string;
  level: SkillLevel;
  percentage: number;
  description: string;
  technologies?: string[]; // 相关技术栈
  projects?: string[]; // 相关项目
  icon?: string; // 图标
  color?: string; // 主题色
}

// 技能分类接口
export interface SkillCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  skills: SkillItem[];
}

// 技能数据
export const skillsData: SkillCategory[] = [
  {
    id: 'frontend',
    name: '前端开发',
    description: '用户界面设计与交互开发',
    icon: '🎨',
    skills: [
      {
        id: 'vue2',
        name: 'Vue 2.x',
        level: 5,
        percentage: 95,
        description: '7年Vue 2.x开发经验，精通Vue全家桶（Vue Router、Vuex），熟练掌握组件化开发、生命周期管理、指令系统等核心概念，具备大型项目架构设计能力。',
        technologies: ['Vue 2.x', 'Vue Router', 'Vuex', 'Vue CLI', 'Vue Devtools'],
        projects: ['医院教育管理系统', '数字货币交易平台', '项目管理系统'],
        icon: '💚',
        color: '#4FC08D'
      },
      {
        id: 'vue3',
        name: 'Vue 3.x',
        level: 4,
        percentage: 85,
        description: '熟练掌握Vue 3 Composition API、响应式系统重构、Teleport、Fragments等新特性，了解Pinia状态管理，具备Vue 2到Vue 3的迁移经验。',
        technologies: ['Vue 3.x', 'Composition API', 'Pinia', 'Vite', 'Vue 3 CLI'],
        projects: ['建筑项目管理系统', '移动端应用', '组件库'],
        icon: '🚀',
        color: '#42b883'
      },
      {
        id: 'react',
        name: 'React',
        level: 3,
        percentage: 75,
        description: '熟悉React Hooks、组件设计模式、状态管理，了解React生态系统，具备React项目开发经验。',
        technologies: ['React', 'React Hooks', 'Redux', 'React Router'],
        projects: ['个人网站', '管理后台', '组件库'],
        icon: '⚛️',
        color: '#61DAFB'
      },
      {
        id: 'nextjs',
        name: 'Next.js',
        level: 3,
        percentage: 70,
        description: '熟悉Next.js全栈开发框架，了解SSR、SSG、API Routes等特性，具备Next.js项目开发和部署经验。',
        technologies: ['Next.js', 'SSR', 'SSG', 'API Routes', 'Vercel'],
        projects: ['个人网站', '全栈应用', '静态网站'],
        icon: '▲',
        color: '#000000'
      },
      {
        id: 'typescript',
        name: 'TypeScript',
        level: 4,
        percentage: 82,
        description: '熟练使用TypeScript进行大型项目开发，掌握类型系统、接口定义、泛型、装饰器等高级特性，能够提升代码质量和开发效率。',
        technologies: ['TypeScript', 'TSConfig', 'Type Guards', 'Generics'],
        projects: ['企业级应用', '组件库', 'Node.js服务'],
        icon: '📘',
        color: '#3178C6'
      },
      {
        id: 'ui-frameworks',
        name: 'UI组件库',
        level: 5,
        percentage: 90,
        description: '精通Element UI、Element Plus、Ant Design、Vant等主流UI组件库，能够快速构建企业级应用界面，具备组件二次封装和主题定制经验。',
        technologies: ['Element UI', 'Element Plus', 'Ant Design', 'Vant', 'uView'],
        projects: ['后台管理系统', '移动端H5', '小程序'],
        icon: '🎨',
        color: '#1890ff'
      },
      {
        id: 'uniapp',
        name: 'UniApp',
        level: 4,
        percentage: 80,
        description: '熟练使用UniApp进行跨平台移动应用开发，具备小程序和App开发经验，能够实现一套代码多端运行。',
        technologies: ['UniApp', 'uView', '微信小程序', 'H5', 'App'],
        projects: ['建筑项目管理移动端', '项目管理小程序'],
        icon: '📱',
        color: '#2B9939'
      },
      {
        id: 'responsive-design',
        name: '响应式设计',
        level: 5,
        percentage: 88,
        description: '熟练掌握响应式布局设计，精通CSS3、Flexbox、Grid布局，具备移动端适配和跨设备兼容性开发经验。',
        technologies: ['CSS3', 'Flexbox', 'Grid', 'Media Queries', 'Mobile First'],
        projects: ['响应式官网', '移动端应用', '跨平台界面'],
        icon: '📱',
        color: '#FF6B6B'
      }
    ]
  },
  {
    id: 'backend',
    name: '后端开发',
    description: '服务器端逻辑与数据处理',
    icon: '⚙️',
    skills: [
      {
        id: 'nodejs',
        name: 'Node.js',
        level: 4,
        percentage: 80,
        description: '熟练使用Node.js和Express框架进行后端开发，具备RESTful API设计和开发经验，了解中间件开发和错误处理机制。',
        technologies: ['Node.js', 'Express', 'npm', 'yarn'],
        projects: ['数字货币交易平台API', '建筑项目管理系统后端', '前端调试工具'],
        icon: '🟢',
        color: '#339933'
      },
      {
        id: 'php',
        name: 'PHP',
        level: 3,
        percentage: 70,
        description: '具备PHP Web开发经验，熟悉ThinkPHP框架开发，了解MVC架构和Web开发流程，有完整的项目开发经验。',
        technologies: ['PHP', 'ThinkPHP', 'MVC', 'Apache'],
        projects: ['医疗美容官网', '商品展示系统'],
        icon: '🐘',
        color: '#777BB4'
      },
      {
        id: 'database',
        name: '数据库技术',
        level: 4,
        percentage: 80,
        description: '熟练使用MySQL数据库进行数据设计和查询优化，掌握Redis缓存应用，具备数据库性能调优和维护经验。',
        technologies: ['MySQL', 'Redis', 'SQL', 'Database Design', 'Query Optimization'],
        projects: ['用户数据管理', '缓存系统设计', '业务数据存储'],
        icon: '🗄️',
        color: '#336791'
      }
    ]
  },
  {
    id: 'tools',
    name: '开发工具',
    description: '提升开发效率的工具和平台',
    icon: '🛠️',
    skills: [
      {
        id: 'git',
        name: '版本控制',
        level: 5,
        percentage: 95,
        description: '精通Git版本控制工具，熟练掌握分支管理、合并策略、冲突解决等操作，具备团队协作和代码管理经验。',
        technologies: ['Git', 'GitHub', 'GitLab', 'SourceTree'],
        projects: ['团队项目协作', '代码版本管理', '分支策略制定'],
        icon: '📝',
        color: '#F05032'
      },
      {
        id: 'build-tools',
        name: '构建工具',
        level: 4,
        percentage: 82,
        description: '熟练使用Webpack、Vite等现代前端构建工具，了解模块打包、代码分割、性能优化等配置。',
        technologies: ['Webpack', 'Vite', 'Vue CLI', 'npm scripts'],
        projects: ['项目构建配置', '性能优化', '开发环境搭建'],
        icon: '⚙️',
        color: '#8DD6F9'
      },
      {
        id: 'data-visualization',
        name: '数据可视化',
        level: 4,
        percentage: 78,
        description: '熟练使用ECharts进行数据可视化开发，能够创建各种图表和大屏展示，具备数据分析和展示经验。',
        technologies: ['ECharts', 'Chart.js', 'D3.js'],
        projects: ['驾驶舱大屏', '业务报表', '实时监控图表'],
        icon: '📊',
        color: '#FF6384'
      },
      {
        id: 'mini-program',
        name: '小程序开发',
        level: 3,
        percentage: 70,
        description: '具备飞书小程序开发经验，了解小程序开发框架和生命周期，能够开发跨平台小程序应用。',
        technologies: ['飞书小程序', 'uniapp', 'uView'],
        projects: ['项目管理小程序', '企业内部应用'],
        icon: '📱',
        color: '#07C160'
      }
    ]
  },
  {
    id: 'soft-skills',
    name: '软技能',
    description: '项目管理与团队协作能力',
    icon: '🤝',
    skills: [
      {
        id: 'project-management',
        name: '项目管理',
        level: 4,
        percentage: 85,
        description: '具备完整项目开发经验，能够独立推进任务进度，从需求分析到项目交付全流程管理，具备时间评估和计划制定能力。',
        technologies: ['项目规划', '任务分解', '进度管理', '风险控制'],
        projects: ['SaaS系统开发', '项目管理系统', '团队协作项目'],
        icon: '📊',
        color: '#4CAF50'
      },
      {
        id: 'communication',
        name: '沟通协作',
        level: 4,
        percentage: 88,
        description: '善于跨部门沟通协调，能够与产品、设计、后端等不同角色协作，具备团队指导和问题解决能力。',
        technologies: ['跨部门协作', '需求沟通', '技术指导', '团队培训'],
        projects: ['产品评审参与', '技术方案讨论', '团队成员指导'],
        icon: '💬',
        color: '#2196F3'
      },
      {
        id: 'problem-solving',
        name: '问题解决',
        level: 5,
        percentage: 90,
        description: '具备强大的技术问题分析和解决能力，擅长调试复杂问题，能够设计创新的技术解决方案。',
        technologies: ['问题分析', '调试技巧', '性能优化', '架构设计'],
        projects: ['复杂Bug修复', '性能瓶颈解决', '技术难题攻克'],
        icon: '🧩',
        color: '#9C27B0'
      }
    ]
  }
];

// 获取技能等级对应的星级显示
export const getSkillStars = (level: SkillLevel): string => {
  return '⭐'.repeat(level);
};

// 获取技能等级对应的文字描述
export const getSkillLevelText = (level: SkillLevel): string => {
  const levelTexts = {
    1: '入门',
    2: '基础',
    3: '熟练',
    4: '精通',
    5: '专家'
  };
  return levelTexts[level];
};

export default skillsData;
