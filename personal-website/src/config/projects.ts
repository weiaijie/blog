/**
 * projects.ts
 *
 * 描述：项目数据配置文件，定义项目案例信息和分类
 *
 * 功能：
 * - 定义项目基本信息和详细描述
 * - 提供项目分类和技术栈信息
 * - 包含项目成果和亮点展示
 *
 * 主要接口/常量：
 * - ProjectItem：项目项目接口
 * - ProjectCategory：项目分类接口
 * - projectsData：项目数据
 *
 * 导出：
 * - 项目相关的类型定义和数据
 */

// 项目状态
export type ProjectStatus = 'completed' | 'in-progress' | 'archived';

// 项目类型
export type ProjectType = 'web-app' | 'mobile-app' | 'desktop-app' | 'library' | 'tool';

// 项目项目接口
export interface ProjectItem {
  id: string;
  name: string;
  description: string;
  detailedDescription: string;
  technologies: string[];
  category: string;
  type: ProjectType;
  status: ProjectStatus;
  startDate: string;
  endDate?: string;
  duration: string;
  role: string;
  teamSize: string;
  highlights: string[];
  challenges: string[];
  solutions: string[];
  results: string[];
  images?: string[];
  demoUrl?: string;
  githubUrl?: string;
  featured: boolean;
  color: string;
  icon: string;
}

// 项目分类接口
export interface ProjectCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  projects: ProjectItem[];
}

// 项目数据
export const projectsData: ProjectCategory[] = [
  {
    id: 'enterprise',
    name: '企业级应用',
    description: '大型企业管理系统和SaaS平台开发',
    icon: '🏢',
    projects: [
      {
        id: 'hospital-education-system',
        name: '医院教育管理系统',
        description: '大型医院教育管理SaaS系统，涵盖学员管理、课程管理、考试评价等完整业务流程',
        detailedDescription: '大型医院教育管理SaaS系统，服务于多家三甲医院的教育培训业务。系统涵盖学员全生命周期管理、课程体系建设、考试评价体系、档案管理等完整业务流程。作为前端技术负责人，主导系统前端架构设计，建立了高效的开发流程和技术规范。',
        technologies: ['Vue 2/3', 'Element UI', 'TypeScript', 'Node.js', 'Express', 'MySQL'],
        category: 'enterprise',
        type: 'web-app',
        status: 'completed',
        startDate: '2022.06',
        endDate: '2024.10',
        duration: '2年4个月',
        role: '前端开发工程师',
        teamSize: '5-8人',
        highlights: [
          '主导前端架构设计，建立基于Vue2/Vue3的组件化开发体系和技术规范',
          '设计并实现动态表单引擎，通过JSON配置驱动复杂表单生成，提升开发效率40%',
          '开发Node.js中间层调试工具，解决前后端分离开发中的调试难题',
          '负责团队技术培训和代码评审，指导2-3名新人快速成长并独立承担开发任务',
          '实施前端性能优化策略，通过组件懒加载、代码分割等手段提升页面加载速度30%',
          '建立前端监控体系，实现错误追踪和性能监控，保障系统稳定运行'
        ],
        challenges: [
          '后端Java服务启动复杂，前端开发调试效率低下',
          '多医院租户数据隔离和细粒度权限控制要求严格',
          '大量复杂表单配置需要高度灵活且易维护的解决方案',
          '团队技术水平参差不齐，需要建立统一的开发规范和培训体系'
        ],
        solutions: [
          '开发Node.js Mock服务和代理工具，实现前端独立开发和调试',
          '设计多租户权限架构，通过路由守卫和组件级权限控制确保数据安全',
          '构建JSON驱动的动态表单系统，支持复杂布局和校验规则配置',
          '建立代码评审机制和技术分享制度，制定前端开发规范和最佳实践'
        ],
        results: [
          '成功交付覆盖多家三甲医院的教育管理系统，用户满意度达95%以上',
          '动态表单系统被复用到其他项目，累计节省开发时间200+小时',
          '前端开发效率提升40%，代码质量和可维护性显著改善',
          '团队成员技术能力快速提升，形成了良好的技术氛围和协作模式'
        ],
        featured: true,
        color: '#1890ff',
        icon: '🏥'
      },
      {
        id: 'construction-project-system',
        name: '建筑项目管理系统',
        description: '专为建筑装修行业开发的项目管理系统，支持项目全生命周期管理',
        detailedDescription: '专为建筑装修行业打造的全栈项目管理解决方案，独立负责系统架构设计和全栈开发。系统采用前后端分离架构，支持PC端管理后台和移动端现场应用，实现了从项目立项到竣工验收的全流程数字化管理。',
        technologies: ['Vue 3', 'TypeScript', 'Ant Design', 'UniApp', 'uView', 'Node.js', 'Express', 'MySQL'],
        category: 'enterprise',
        type: 'web-app',
        status: 'completed',
        startDate: '2021.09',
        endDate: '2022.05',
        duration: '8个月',
        role: '全栈开发工程师',
        teamSize: '1人（独立开发）',
        highlights: [
          '独立完成系统架构设计，包括数据库设计、API接口规划和前端架构设计',
          '开发PC端管理后台（Vue3 + Ant-Design）和移动端应用（UniApp + uView）',
          '设计并实现复杂的Excel批量导入引擎，支持三层关系任务数据的智能解析',
          '开发交互式甘特图组件，支持拖拽调整、依赖关系管理和进度实时同步',
          '构建Node.js + Express + MySQL后端服务，实现RESTful API和数据管理',
          '移动端应用实现离线缓存和数据同步，保障现场作业的连续性'
        ],
        challenges: [
          '复杂Excel表格包含三层嵌套任务关系，需要智能识别合并单元格结构',
          '大批量任务数据导入时的事务一致性和错误处理机制',
          'PC端和移动端数据实时同步，以及移动端离线作业支持',
          '甘特图组件的性能优化，支持大量任务的流畅交互'
        ],
        solutions: [
          '开发Excel解析引擎，通过算法识别合并单元格并重构数据关系',
          '实现分批导入和事务回滚机制，确保数据完整性和系统稳定性',
          '采用WebSocket实现实时数据推送，UniApp本地存储支持离线操作',
          '优化甘特图渲染算法，使用虚拟滚动和懒加载提升大数据量性能'
        ],
        results: [
          '成功交付完整的项目管理解决方案，获得客户高度认可',
          '移动端应用使现场作业效率提升50%，大幅减少沟通成本',
          'Excel导入功能处理复杂项目数据准确率达99%以上',
          '系统稳定运行，支持多项目并行管理，为装修行业数字化转型提供有力支撑'
        ],
        featured: true,
        color: '#52c41a',
        icon: '📊'
      }
    ]
  },
  {
    id: 'business-systems',
    name: '业务系统',
    description: '各类业务管理系统和平台开发',
    icon: '💼',
    projects: [
      {
        id: 'trading-platform',
        name: '数字货币交易平台后台管理系统',
        description: '数字货币交易所后台管理系统，为运营团队提供用户管理、数据统计等功能',
        detailedDescription: '大型数字货币交易平台的核心管理系统，负责全栈开发和架构设计。系统承载5-6万注册用户和300+内部运营人员的业务需求，涵盖用户生命周期管理、精细化权限控制、营销活动策划、理财产品管理等核心业务模块。',
        technologies: ['Vue 2', 'Element UI', 'ECharts', 'Node.js', 'Express', 'MySQL', 'Redis'],
        category: 'business-systems',
        type: 'web-app',
        status: 'completed',
        startDate: '2019.10',
        endDate: '2021.06',
        duration: '1年8个月',
        role: '全栈开发工程师',
        teamSize: '4-6人',
        highlights: [
          '设计并实现企业级权限管理架构，支持10+种角色和50+种权限的灵活组合',
          '开发用户全生命周期管理系统，包括注册、认证、风控、客服等完整流程',
          '构建营销活动管理平台，支持多样化活动策略和精准用户触达',
          '开发理财产品管理系统，实现产品配置、收益计算、风险控制等核心功能',
          '使用ECharts构建数据可视化驾驶舱，实时展示关键业务指标和趋势分析',
          '建立全方位系统监控体系，包括性能监控、错误追踪、业务预警等'
        ],
        challenges: [
          '金融级安全要求下的细粒度权限控制和数据隔离',
          '高并发场景下的系统性能优化和稳定性保障',
          '复杂业务逻辑的模块化设计和代码可维护性',
          '大量实时数据的处理和可视化展示性能优化'
        ],
        solutions: [
          '采用RBAC权限模型，结合自定义指令实现DOM级别的权限控制',
          '实施多层次性能优化策略：代码分割、懒加载、缓存优化、数据库查询优化',
          '建立模块化架构和组件库，制定统一的开发规范和最佳实践',
          '优化数据查询和图表渲染算法，使用虚拟滚动和分页加载提升性能'
        ],
        results: [
          '成功支撑5-6万用户的平台运营，系统稳定性达99.9%以上',
          '通过全面性能优化，页面加载时间从4s缩短至1s，接口响应速度提升60%',
          '权限系统灵活性和安全性得到业务方高度认可，支撑复杂的运营需求',
          '数据可视化系统为业务决策提供有力支撑，提升运营效率30%以上'
        ],
        featured: false,
        color: '#722ed1',
        icon: '💱'
      }
    ]
  },
  {
    id: 'web-development',
    name: 'Web开发',
    description: '网站开发和维护项目',
    icon: '🌐',
    projects: [
      {
        id: 'medical-beauty-website',
        name: '医疗美容官网和商品展示系统',
        description: '上海欧莱美医疗美容医院官网和医美商品展示系统开发',
        detailedDescription: '医疗美容行业的数字化展示平台，独立负责官网开发和商品展示系统建设。项目严格遵循医疗行业规范，在确保合规性的前提下，为医院提供专业的线上品牌展示和服务介绍平台。',
        technologies: ['JavaScript', 'Vue', 'HTML/CSS', 'ThinkPHP', 'MySQL'],
        category: 'web-development',
        type: 'web-app',
        status: 'completed',
        startDate: '2018.05',
        endDate: '2019.08',
        duration: '1年3个月',
        role: 'Web开发工程师',
        teamSize: '1人（独立开发）',
        highlights: [
          '独立完成医院官网的UI设计和前端开发，实现响应式布局和交互效果',
          '参考草场地商城APP的设计理念，开发符合医疗行业特色的商品展示系统',
          '实现商品分类管理、多维度筛选、详情展示等完整功能模块',
          '基于ThinkPHP框架构建后台内容管理系统，支持商品信息的CRUD操作',
          '建立网站运维流程，负责内容更新、性能监控和安全维护',
          '严格遵循医疗广告法规，确保网站内容的合规性和专业性'
        ],
        challenges: [
          '医疗行业严格的广告法规限制，需要在展示效果和合规性之间找到平衡',
          '跨设备兼容性要求高，需要确保在各种终端上的一致体验',
          '商品展示系统的用户体验设计，既要美观又要符合医疗行业的专业性',
          '作为职业生涯初期项目，需要快速学习和掌握全栈开发技能'
        ],
        solutions: [
          '深入研究医疗广告法规，建立内容审核机制，确保所有展示内容合规',
          '采用渐进式增强的响应式设计策略，优先保证核心功能的跨设备兼容',
          '参考优秀医疗网站和电商平台的设计模式，形成符合行业特色的设计规范',
          '制定学习计划，系统掌握前后端开发技术，建立完整的技术知识体系'
        ],
        results: [
          '成功交付符合医疗行业规范的官网和商品展示系统，获得客户认可',
          '建立了完整的Web开发技能体系，为后续全栈发展奠定坚实基础',
          '积累了医疗行业项目经验，深入理解行业特殊性和合规要求',
          '培养了独立项目管理和问题解决能力，为职业发展打下良好基础'
        ],
        featured: false,
        color: '#eb2f96',
        icon: '🏥'
      },
      {
        id: 'personal-website',
        name: '个人网站',
        description: '基于Next.js的个人展示网站，采用现代化设计和技术栈',
        detailedDescription: '一个现代化的个人展示网站，采用Next.js全栈框架开发，具备完整的响应式设计、主题切换、动画效果等功能。网站展示了个人技能、项目经验和博客文章。',
        technologies: ['Next.js', 'React', 'TypeScript', 'Framer Motion', 'CSS Modules'],
        category: 'web-development',
        type: 'web-app',
        status: 'in-progress',
        startDate: '2024.01',
        duration: '进行中',
        role: '全栈开发工程师',
        teamSize: '1人',
        highlights: [
          '采用Next.js全栈框架开发',
          '实现了完整的响应式设计',
          '集成了主题切换和动画效果',
          '支持博客文章和项目展示'
        ],
        challenges: [
          '需要平衡设计美观性和性能',
          '确保在各种设备上的兼容性'
        ],
        solutions: [
          '采用苹果风格的简约设计理念',
          '使用现代化的前端技术栈和最佳实践'
        ],
        results: [
          '创建了一个专业的个人展示平台',
          '展示了现代Web开发技能和经验'
        ],
        featured: true,
        color: '#13c2c2',
        icon: '👨‍💻'
      }
    ]
  }
];

// 获取所有项目
export const getAllProjects = (): ProjectItem[] => {
  return projectsData.flatMap(category => category.projects);
};

// 获取精选项目
export const getFeaturedProjects = (): ProjectItem[] => {
  return getAllProjects().filter(project => project.featured);
};

// 根据分类获取项目
export const getProjectsByCategory = (categoryId: string): ProjectItem[] => {
  const category = projectsData.find(cat => cat.id === categoryId);
  return category ? category.projects : [];
};

// 根据ID获取项目
export const getProjectById = (projectId: string): ProjectItem | undefined => {
  return getAllProjects().find(project => project.id === projectId);
};

export default projectsData;
