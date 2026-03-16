/**
 * projects.tsx
 *
 * 描述：项目案例页，默认展示摘要，点击后通过弹窗查看完整案例分析
 */

import Head from 'next/head';
import { useEffect, useState } from 'react';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/Projects.module.css';
import { projectCaseStudies, projectCategories, type ProjectCaseStudy } from '@/data/projects';

export default function Projects() {
  const [activeCategory, setActiveCategory] = useState('all');
  const [selectedProject, setSelectedProject] = useState<ProjectCaseStudy | null>(null);

  const filteredProjects =
    activeCategory === 'all'
      ? projectCaseStudies
      : projectCaseStudies.filter((project) => project.category === activeCategory);

  useEffect(() => {
    if (!selectedProject) {
      document.body.style.removeProperty('overflow');
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedProject(null);
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.removeProperty('overflow');
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedProject]);

  useEffect(() => {
    if (selectedProject && !filteredProjects.some((project) => project.id === selectedProject.id)) {
      setSelectedProject(null);
    }
  }, [filteredProjects, selectedProject]);

  return (
    <>
      <Head>
        <title>项目案例 - saber的个人网站</title>
        <meta
          name="description"
          content="项目案例页，展示系统对接、企业小程序和企业福利商城改造等真实项目案例分析。"
        />
      </Head>
      <Layout>
        <div className={styles.projectsPage}>
          <div className={styles.container}>
            <div className={styles.hero}>
              <p className={styles.eyebrow}>Project Case Studies</p>
              <h1 className={styles.pageTitle}>项目案例</h1>
              <p className={styles.pageDescription}>
                这里整理的是我做过的一些真实项目案例。列表页先展示每个项目的核心信息，想看完整背景、问题拆解和最终结果时，可以继续展开查看详情。
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

            <div className={styles.projectsGrid}>
              {filteredProjects.map((project) => (
                <article className={styles.projectCard} key={project.id}>
                  <div className={styles.projectHeader}>
                    <div className={styles.projectHeaderTop}>
                      <span className={styles.projectCategory}>{project.categoryLabel}</span>
                      <span className={styles.projectYear}>{project.year}</span>
                    </div>
                    <h2 className={styles.projectTitle}>{project.title}</h2>
                    <p className={styles.projectSubtitle}>{project.subtitle}</p>
                    <p className={styles.projectDescription}>{project.summary}</p>
                    <p className={styles.projectPositioning}>{project.positioning}</p>
                  </div>

                  <div className={styles.projectContent}>
                    <div className={styles.projectTags}>
                      {project.tags.slice(0, 6).map((tag) => (
                        <span className={styles.projectTag} key={tag}>
                          {tag}
                        </span>
                      ))}
                    </div>

                    <div className={styles.highlights}>
                      {project.highlights.map((item) => (
                        <span className={styles.highlightItem} key={item}>
                          {item}
                        </span>
                      ))}
                    </div>

                    <div className={styles.projectActions}>
                      <button
                        type="button"
                        className={styles.detailButton}
                        onClick={() => setSelectedProject(project)}
                      >
                        查看详细案例
                      </button>
                      {project.links.slice(0, 2).map((link) => (
                        <a
                          key={link.url}
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.projectLink}
                        >
                          {link.label}
                        </a>
                      ))}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>

        {selectedProject ? (
          <div
            className={styles.modalOverlay}
            role="presentation"
            onClick={() => setSelectedProject(null)}
          >
            <div
              className={styles.modalCard}
              role="dialog"
              aria-modal="true"
              aria-labelledby="project-modal-title"
              onClick={(event) => event.stopPropagation()}
            >
              <div className={styles.modalHeader}>
                <div className={styles.projectHeaderTop}>
                  <span className={styles.projectCategory}>{selectedProject.categoryLabel}</span>
                  <span className={styles.projectYear}>{selectedProject.year}</span>
                </div>
                <button
                  type="button"
                  className={styles.modalClose}
                  aria-label="关闭项目详情"
                  onClick={() => setSelectedProject(null)}
                >
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                <h2 id="project-modal-title" className={styles.projectTitle}>
                  {selectedProject.title}
                </h2>
                <p className={styles.projectSubtitle}>{selectedProject.subtitle}</p>
                <p className={styles.projectDescription}>{selectedProject.summary}</p>
                <p className={styles.projectPositioning}>{selectedProject.positioning}</p>

                <div className={styles.projectTags}>
                  {selectedProject.tags.map((tag) => (
                    <span className={styles.projectTag} key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>

                {selectedProject.links.length ? (
                  <div className={styles.projectLinks}>
                    {selectedProject.links.map((link) => (
                      <a
                        key={link.url}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.projectLink}
                      >
                        {link.label}
                      </a>
                    ))}
                  </div>
                ) : null}

                <div className={styles.highlights}>
                  {selectedProject.highlights.map((item) => (
                    <span className={styles.highlightItem} key={item}>
                      {item}
                    </span>
                  ))}
                </div>

                <div className={styles.sections}>
                  {selectedProject.sections.map((section) => (
                    <section className={styles.sectionBlock} key={section.title}>
                      <h3 className={styles.sectionTitle}>{section.title}</h3>
                      <ul className={styles.sectionList}>
                        {section.items.map((item) => (
                          <li className={styles.sectionItem} key={item}>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </Layout>
    </>
  );
}
