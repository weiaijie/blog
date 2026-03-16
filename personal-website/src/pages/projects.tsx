/**
 * projects.tsx
 *
 * 描述：项目案例页，展示真实项目的案例分析内容
 */

import Head from 'next/head';
import { useState } from 'react';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/Projects.module.css';
import { projectCaseStudies, projectCategories } from '@/data/projects';

export default function Projects() {
  const [activeCategory, setActiveCategory] = useState('all');

  const filteredProjects =
    activeCategory === 'all'
      ? projectCaseStudies
      : projectCaseStudies.filter((project) => project.category === activeCategory);

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
                这里整理的是我做过的一些真实项目案例，不只是项目名称的简单罗列。每个案例都会从项目背景、遇到的问题、解决思路和最终结果几个方面展开，希望更清楚地展示我的项目经验和实际解决问题的能力。
              </p>
            </div>

            <div className={styles.categoryFilter}>
              {projectCategories.map((category) => (
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
                      {project.tags.map((tag) => (
                        <span className={styles.projectTag} key={tag}>
                          {tag}
                        </span>
                      ))}
                    </div>

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
                        </a>
                      ))}
                    </div>

                    <div className={styles.highlights}>
                      {project.highlights.map((item) => (
                        <span className={styles.highlightItem} key={item}>
                          {item}
                        </span>
                      ))}
                    </div>

                    <div className={styles.sections}>
                      {project.sections.map((section) => (
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
                </article>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
