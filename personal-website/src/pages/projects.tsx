/**
 * projects.tsx
 *
 * 描述：项目案例页，默认展示摘要，点击后通过弹窗查看完整案例分析
 */

import { useEffect, useState } from 'react';
import Layout from '@/components/layout/Layout';
import SeoHead from '@/components/common/SeoHead';
import styles from '@/styles/Projects.module.css';
import { projectCaseStudies, projectCategories, type ProjectCaseStudy } from '@/data/projects';

export default function Projects() {
  const [activeCategory, setActiveCategory] = useState('all');

  const filteredProjects =
    activeCategory === 'all'
      ? projectCaseStudies
      : projectCaseStudies.filter((project) => project.category === activeCategory);

  return (
    <>
      <SeoHead
        title="项目案例 - 许辉"
        description="整理许辉参与过的系统对接、企业小程序、福利商城和后台系统项目。"
        path="/projects/"
      />
      <Layout>
        <div className={styles.projectsPage}>
          <div className={styles.container}>
            <div className={styles.hero}>
              <h1 className={styles.pageTitle}>项目案例</h1>
              <p className={styles.pageDescription}>
                这里放一些我实际做过、维护过的项目。尽量少写套话，多写当时要解决什么、我负责哪块。
              </p>
            </div>

            <div className={styles.categoryFilter}>
              {projectCategories.map((category) => (
                <button
                  key={category.id}
                  type="button"
                  className={`${styles.categoryButton} ${activeCategory === category.id ? styles.active : ''}`}
                  onClick={() => setActiveCategory(category.id)}
                >
                  {category.name}
                </button>
              ))}
            </div>

            <div className={styles.projectsList}>
              {filteredProjects.map((project) => (
                <article className={styles.projectItem} key={project.id}>
                  <div className={styles.projectHeader}>
                    <h2 className={styles.projectTitle}>{project.title}</h2>
                    <div className={styles.projectMeta}>
                      <span className={styles.projectYear}>{project.year}</span>
                      <span className={styles.projectCategory}>{project.categoryLabel}</span>
                    </div>
                    <div className={styles.projectTags}>
                      {project.tags.map((tag) => (
                        <span className={styles.projectTag} key={tag}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className={styles.projectContent}>
                    <div className={styles.projectText}>
                      <p>{project.summary}</p>
                      <p>{project.positioning}</p>
                    </div>

                    <div className={styles.projectHighlights}>
                      <h3 className={styles.highlightsTitle}>我主要处理的部分</h3>
                      <ul className={styles.highlightsList}>
                        {project.highlights.map((item) => (
                          <li key={item}>
                            <svg className={styles.checkIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {project.links.length > 0 && (
                      <div className={styles.projectLinks}>
                        {project.links.map((link) => (
                          <a
                            key={link.url}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.projectLink}
                          >
                            {link.label}
                            <svg className={styles.linkIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <line x1="5" y1="12" x2="19" y2="12"></line>
                              <polyline points="12 5 19 12 12 19"></polyline>
                            </svg>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
