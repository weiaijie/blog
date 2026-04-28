import Layout from '@/components/layout/Layout';
import siteConfig from '@/config/site';
import SeoHead from '@/components/common/SeoHead';
import styles from '@/styles/About.module.css';

export default function About() {
  return (
    <>
      <SeoHead
        title="关于我 - 许辉"
        description="了解许辉的项目经历、技术栈、交付方式，以及在企业后台、小程序和系统对接项目中的真实经验。"
        path="/about/"
      />
      <Layout>
        <div className={styles.aboutPage}>
          <div className={styles.container}>
            <div className={styles.hero}>
              <h1 className={styles.pageTitle}>关于我</h1>
            </div>

            <div className={styles.layout}>
              {/* 左侧边栏：基本信息与技能 */}
              <aside className={styles.sidebar}>
                <div className={styles.sidebarSticky}>
                  <div className={styles.sidebarBlock}>
                    <h3 className={styles.sidebarTitle}>联系方式</h3>
                    <ul className={styles.contactList}>
                      <li>
                        <span className={styles.contactLabel}>Email</span>
                        <a href={`mailto:${siteConfig.contact.email}`}>{siteConfig.contact.email}</a>
                      </li>
                      <li>
                        <span className={styles.contactLabel}>Phone</span>
                        <a href={`tel:${siteConfig.contact.phone}`}>{siteConfig.contact.phone}</a>
                      </li>
                      <li>
                        <span className={styles.contactLabel}>Location</span>
                        <span>{siteConfig.contact.location}</span>
                      </li>
                      <li>
                        <span className={styles.contactLabel}>GitHub</span>
                        <a href={siteConfig.social.github.url} target="_blank" rel="noopener noreferrer">
                          @{siteConfig.social.github.username}
                        </a>
                      </li>
                    </ul>
                  </div>

                  <div className={styles.sidebarBlock}>
                    <h3 className={styles.sidebarTitle}>技能专长</h3>
                    <div className={styles.skillGroups}>
                      {siteConfig.profile.skillGroups.map((group) => (
                        <div key={group.title} className={styles.skillGroup}>
                          <h4 className={styles.skillGroupTitle}>{group.title}</h4>
                          <div className={styles.skillTags}>
                            {group.items.map((item) => (
                              <span key={item} className={styles.skillTag}>{item}</span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </aside>

              {/* 右侧主内容区：自述与工作经历 */}
              <main className={styles.mainContent}>
                <section className={styles.section}>
                  <h2 className={styles.sectionTitle}>个人自述</h2>
                  <div className={styles.introText}>
                    {siteConfig.profile.aboutIntro.map((paragraph, index) => (
                      <p key={index}>{paragraph}</p>
                    ))}
                  </div>
                </section>

                <section className={styles.section}>
                  <h2 className={styles.sectionTitle}>工作经历</h2>
                  <div className={styles.timeline}>
                    {siteConfig.profile.experience.map((item, index) => (
                      <div key={`${item.company}-${index}`} className={styles.timelineItem}>
                        <div className={styles.timelineHeader}>
                          <div className={styles.timelineHeaderLeft}>
                            <h3 className={styles.timelineRole}>{item.role}</h3>
                            <div className={styles.timelineCompany}>{item.company}</div>
                          </div>
                          <div className={styles.timelinePeriod}>{item.period}</div>
                        </div>
                        
                        <div className={styles.timelineBody}>
                          <div className={styles.timelineProject}>
                            <strong>核心项目：</strong>{item.project}
                          </div>
                          <ul className={styles.timelineHighlights}>
                            {item.highlights.map((highlight, hIndex) => (
                              <li key={hIndex}>{highlight}</li>
                            ))}
                          </ul>
                          <div className={styles.timelineTech}>
                            <strong>技术栈：</strong>{item.techStack}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className={styles.section}>
                  <h2 className={styles.sectionTitle}>教育背景</h2>
                  <div className={styles.educationItem}>
                    <div className={styles.educationHeader}>
                      <h3 className={styles.educationDegree}>{siteConfig.profile.education.degree}</h3>
                      <div className={styles.educationPeriod}>{siteConfig.profile.education.period}</div>
                    </div>
                    <div className={styles.educationSchool}>{siteConfig.profile.education.school}</div>
                  </div>
                </section>
              </main>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
