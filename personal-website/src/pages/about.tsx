import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import siteConfig from '@/config/site';
import styles from '@/styles/About.module.css';

export default function About() {
  return (
    <>
      <Head>
        <title>关于我 - {siteConfig.title}</title>
        <meta
          name="description"
          content="7年全栈开发经验，聚焦 Vue 生态、复杂业务系统、跨端应用与工程化建设。"
        />
      </Head>
      <Layout>
        <div className={styles.aboutPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>关于我</h1>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>个人介绍</h2>
              <div className={styles.profileContent}>
                <div className={styles.profileText}>
                  {siteConfig.profile.aboutIntro.map((paragraph) => (
                    <p key={paragraph} className={styles.paragraph}>
                      {paragraph}
                    </p>
                  ))}
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>核心技能</h2>
              <div className={styles.profileContent}>
                <div className={styles.profileText}>
                  {siteConfig.profile.skillGroups.map((group) => (
                    <p key={group.title} className={styles.paragraph}>
                      <strong>{group.title}：</strong>
                      {group.items.join('、')}
                    </p>
                  ))}
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>工作经历</h2>
              <div className={styles.timeline}>
                {siteConfig.profile.experience.map((item) => (
                  <div key={`${item.company}-${item.period}`} className={styles.timelineItem}>
                    <div className={styles.timelineDot}></div>
                    <div className={styles.timelineContent}>
                      <h3 className={styles.timelineTitle}>{item.role}</h3>
                      <p className={styles.timelineSubtitle}>
                        {item.company} | {item.period}
                      </p>
                      <p className={styles.timelineText}>
                        <strong>项目：</strong>
                        {item.project}
                      </p>
                      <p className={styles.timelineText}>
                        <strong>技术栈：</strong>
                        {item.techStack}
                      </p>
                      {item.highlights.map((highlight) => (
                        <p key={highlight} className={styles.timelineText}>
                          • {highlight}
                        </p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>教育背景</h2>
              <div className={styles.timeline}>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.timelineTitle}>{siteConfig.profile.education.degree}</h3>
                    <p className={styles.timelineSubtitle}>
                      {siteConfig.profile.education.school} | {siteConfig.profile.education.period}
                    </p>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </Layout>
    </>
  );
}
