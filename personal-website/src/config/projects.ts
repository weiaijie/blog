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
        id: 'saas-management-system',
        name: 'SaaS后台管理系统',
        description: '医院进修生SaaS后台管理系统，为多家医院提供全功能管理解决方案',
        detailedDescription: '这是一款为多家医院量身定制的全功能后台管理系统，旨在满足医院进修生和医师的招录、培训、课程和考试等多方面需求。系统采用现代化的前端技术栈，提供了完整的用户管理、权限控制、数据可视化等功能。',
        technologies: ['Vue 2', 'Element UI', 'Vant', 'Node.js', 'Express', 'MySQL', 'ECharts'],
        category: 'enterprise',
        type: 'web-app',
        status: 'completed',
        startDate: '2022.06',
        endDate: '2024.08',
        duration: '2年2个月',
        role: '前端开发工程师',
        teamSize: '5-8人',
        highlights: [
          '支持多家医院的进修生招录和管理',
          '实现了形成性评价系统，支持自评、互评和上级评价',
          '开发了驾驶舱大屏，提供数据可视化展示',
          '设计了可配置的个人信息管理模块',
          '集成了完整的课程中心和考试系统'
        ],
        challenges: [
          '部分功能采用Java模板引擎开发，前后端耦合度高',
          '多医院数据隔离和权限管理复杂',
          '大量表单配置需要灵活的解决方案'
        ],
        solutions: [
          '引入Node.js和Express创建本地文件抓取和接口转发服务',
          '通过JSON配置实现动态表单字段和布局',
          '设计了统一的权限管理和数据隔离机制'
        ],
        results: [
          '成功为多家医院提供了完整的进修生管理解决方案',
          '提高了前端团队的开发效率',
          '减少了前后端配置的复杂性'
        ],
        featured: true,
        color: '#1890ff',
        icon: '🏥'
      },
      {
        id: 'project-management-system',
        name: '项目管理系统',
        description: '专注于别墅装修项目的管理系统，通过严密的任务排期流程优化项目管理',
        detailedDescription: '一款专为别墅装修行业设计的项目管理系统，主要目标是通过严密的任务排期流程来优化项目的管理效率。系统支持PC端和移动端（飞书小程序），提供了完整的项目生命周期管理功能。',
        technologies: ['Vue 3', 'TypeScript', 'Ant Design', 'uniapp', 'uView', 'Node.js', 'Express', 'MySQL', 'xlsx'],
        category: 'enterprise',
        type: 'web-app',
        status: 'completed',
        startDate: '2021.09',
        endDate: '2022.06',
        duration: '9个月',
        role: '前端开发工程师',
        teamSize: '3-5人',
        highlights: [
          '支持PC端和飞书小程序双端开发',
          '实现了复杂的Excel表格数据导入处理',
          '开发了可视化的甘特图排期功能',
          '提供了完整的任务提交与审核流程'
        ],
        challenges: [
          '表格导入包含三层关系的排期任务，关系通过合并单元格表示',
          '大量排期任务的提交上传容易丢失数据'
        ],
        solutions: [
          '通过xlsx插件提取必要信息，解决复杂表格数据处理问题',
          '使用回调函数机制逐条提交任务，实时记录状态并显示进度'
        ],
        results: [
          '极大提高了用户体验和数据完整性',
          '成功解决了复杂业务场景下的数据处理问题',
          '为装修行业提供了高效的项目管理解决方案'
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
        name: '交易所中台系统',
        description: '多渠道交易所的中台管理系统，支持渠道配置和业务报表',
        detailedDescription: '一个为交易所设计的多渠道中台系统，提供了完整的渠道管理、配置信息维护、业务报表等功能。系统采用Vue 2技术栈，注重用户体验和数据展示。',
        technologies: ['Vue 2', 'Element UI', 'ECharts', 'Node.js', 'Express', 'MySQL'],
        category: 'business-systems',
        type: 'web-app',
        status: 'completed',
        startDate: '2019.10',
        endDate: '2020.04',
        duration: '6个月',
        role: '前端开发工程师',
        teamSize: '4-6人',
        highlights: [
          '支持多渠道的配置信息管理',
          '实现了渠道首页轮播图上传替换功能',
          '开发了完整的业务报表模块',
          '提供了灵活的表单配置解决方案'
        ],
        challenges: [
          '配置信息的表单数据较多，维护复杂'
        ],
        solutions: [
          '将表单类型封装成组件，用数组对象方式存放表单参数',
          '提高了表单的可维护性和复用性'
        ],
        results: [
          '成功简化了复杂表单的维护工作',
          '提升了系统的可扩展性和用户体验'
        ],
        featured: false,
        color: '#722ed1',
        icon: '💱'
      },
      {
        id: 'trading-management',
        name: '交易所管理系统',
        description: '多渠道交易所的后台管理系统，包含用户管理、权限控制等功能',
        detailedDescription: '一个功能完整的多渠道交易所管理系统，提供了用户信息管理、实名审核、交易记录查询、权限管理等核心功能。系统注重安全性和性能优化。',
        technologies: ['Vue 2', 'Element UI', 'ECharts', 'Node.js', 'Express', 'MySQL'],
        category: 'business-systems',
        type: 'web-app',
        status: 'completed',
        startDate: '2019.10',
        endDate: '2021.06',
        duration: '1年8个月',
        role: '前端开发工程师',
        teamSize: '4-6人',
        highlights: [
          '开发了各种交易记录的查询页面',
          '使用ECharts实现首页图表展示功能',
          '负责用户信息管理和实名审核模块',
          '参与了细粒度权限功能的设计研发'
        ],
        challenges: [
          '系统需要很细的权限控制',
          '首屏加载速度较慢，白屏时间较长'
        ],
        solutions: [
          '通过自定义指令在DOM层面控制权限，删除不满足权限的元素',
          '使用包分析器优化插件按需引入和路由懒加载'
        ],
        results: [
          '实现了精细化的权限控制系统',
          '将白屏时间从4秒减少到1秒左右',
          '显著提升了系统性能和用户体验'
        ],
        featured: false,
        color: '#fa8c16',
        icon: '🏦'
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
        id: 'medical-website',
        name: '医疗美容官网',
        description: '上海欧莱美医疗美容医院官网开发和维护',
        detailedDescription: '负责上海欧莱美医疗美容医院官网的开发和维护工作，包括管理后台、移动端功能开发，以及日常的网站维护和更新。',
        technologies: ['JavaScript', 'Vue', 'Element UI', 'Vant', 'PHP'],
        category: 'web-development',
        type: 'web-app',
        status: 'completed',
        startDate: '2018.05',
        endDate: '2019.08',
        duration: '1年3个月',
        role: '前端开发工程师',
        teamSize: '2-3人',
        highlights: [
          '负责管理后台和移动端功能开发',
          '根据设计图完成静态页面编写',
          '完成前后端联调和功能测试',
          '负责网站的日常维护和更新'
        ],
        challenges: [
          '需要同时兼顾PC端和移动端的开发',
          '医疗行业对网站合规性要求较高'
        ],
        solutions: [
          '采用响应式设计和移动端适配方案',
          '严格按照医疗行业规范进行开发'
        ],
        results: [
          '成功交付了功能完整的医疗美容官网',
          '获得了宝贵的行业项目开发经验'
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
