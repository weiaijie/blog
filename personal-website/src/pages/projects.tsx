import Head from 'next/head';
import { useState } from 'react';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/Projects.module.css';

interface Project {
  id: string;
  title: string;
  description: string;
  image: string;
  category: string;
  tags: string[];
  link?: string;
  github?: string;
}

export default function Projects() {
  // 项目分类
  const categories = [
    { id: 'all', name: '全部' },
    { id: 'web', name: '网站开发' },
    { id: 'app', name: '应用程序' },
    { id: 'design', name: '设计项目' },
    { id: 'opensource', name: '开源贡献' },
  ];

  // 示例项目数据
  const allProjects: Project[] = [
    {
      id: 'project-1',
      title: '智能家居控制系统',
      description: '基于React和Node.js的智能家居控制平台，支持多设备管理和自动化场景设置',
      image: '/placeholder-project.jpg',
      category: 'web',
      tags: ['React', 'Node.js', 'IoT'],
      link: 'https://example.com/project1',
      github: 'https://github.com/username/project1'
    },
    {
      id: 'project-2',
      title: '电子商务平台',
      description: '全栈电商网站，包含商品展示、购物车、支付集成和订单管理功能',
      image: '/placeholder-project.jpg',
      category: 'web',
      tags: ['Vue.js', 'Express', 'MongoDB'],
      link: 'https://example.com/project2',
      github: 'https://github.com/username/project2'
    },
    {
      id: 'project-3',
      title: '数据可视化仪表板',
      description: '企业级数据分析和可视化平台，支持多种图表类型和实时数据更新',
      image: '/placeholder-project.jpg',
      category: 'web',
      tags: ['D3.js', 'TypeScript', 'GraphQL'],
      link: 'https://example.com/project3'
    },
    {
      id: 'project-4',
      title: '移动健康应用',
      description: '帮助用户跟踪健康数据和运动记录的移动应用，支持数据同步和分析',
      image: '/placeholder-project.jpg',
      category: 'app',
      tags: ['React Native', 'Firebase', 'Health API'],
      link: 'https://example.com/project4',
      github: 'https://github.com/username/project4'
    },
    {
      id: 'project-5',
      title: '企业品牌重塑',
      description: '为某科技公司进行的品牌重塑项目，包括标志设计、色彩系统和品牌指南',
      image: '/placeholder-project.jpg',
      category: 'design',
      tags: ['品牌设计', 'UI/UX', 'Figma'],
      link: 'https://example.com/project5'
    },
    {
      id: 'project-6',
      title: 'React组件库',
      description: '开源的React UI组件库，提供了一套符合设计规范的可复用组件',
      image: '/placeholder-project.jpg',
      category: 'opensource',
      tags: ['React', 'TypeScript', 'Storybook'],
      github: 'https://github.com/username/project6'
    }
  ];

  // 状态管理
  const [activeCategory, setActiveCategory] = useState('all');
  
  // 根据分类筛选项目
  const filteredProjects = activeCategory === 'all' 
    ? allProjects 
    : allProjects.filter(project => project.category === activeCategory);

  return (
    <>
      <Head>
        <title>项目 - saber的个人网站</title>
        <meta name="description" content="我的项目作品集，包括网站开发、应用程序和设计项目" />
      </Head>
      <Layout>
        <div className={styles.projectsPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>项目</h1>
            
            <div className={styles.categoryFilter}>
              {categories.map(category => (
                <button
                  key={category.id}
                  className={`${styles.categoryButton} ${activeCategory === category.id ? styles.active : ''}`}
                  onClick={() => setActiveCategory(category.id)}
                >
                  {category.name}
                </button>
              ))}
            </div>
            
            <div className={styles.projectsGrid}>
              {filteredProjects.map(project => (
                <div className={styles.projectCard} key={project.id}>
                  <div className={styles.projectImageContainer}>
                    <div className={styles.projectImage}>
                      {/* 项目图片占位符 */}
                      <div className={styles.placeholder}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                          <circle cx="8.5" cy="8.5" r="1.5"></circle>
                          <polyline points="21 15 16 10 5 21"></polyline>
                        </svg>
                      </div>
                    </div>
                  </div>
                  <div className={styles.projectContent}>
                    <h2 className={styles.projectTitle}>{project.title}</h2>
                    <p className={styles.projectDescription}>{project.description}</p>
                    <div className={styles.projectTags}>
                      {project.tags.map((tag, index) => (
                        <span className={styles.projectTag} key={index}>{tag}</span>
                      ))}
                    </div>
                    <div className={styles.projectLinks}>
                      {project.link && (
                        <a href={project.link} target="_blank" rel="noopener noreferrer" className={styles.projectLink}>
                          查看项目
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.linkIcon}>
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                          </svg>
                        </a>
                      )}
                      {project.github && (
                        <a href={project.github} target="_blank" rel="noopener noreferrer" className={styles.projectLink}>
                          GitHub
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.linkIcon}>
                            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                          </svg>
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
