import Layout from '@/components/layout/Layout';
import SeoHead from '@/components/common/SeoHead';
import siteConfig from '@/config/site';
import styles from '@/styles/Contact.module.css';

export default function Contact() {
  return (
    <>
      <SeoHead
        title="联系 - 许辉"
        description="通过邮件或 GitHub 联系许辉，讨论企业后台、小程序、官网展示站、系统对接和项目迭代合作。"
        path="/contact/"
      />
      <Layout>
        <div className={styles.contactPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>联系我</h1>

            <div className={styles.contactContent}>
              <div className={styles.contactInfo}>
                <p className={styles.contactText}>
                  如果你想聊项目合作、现有系统迭代、问题排查，或者只是想确认需求是否值得做，直接发邮件会更高效。
                </p>

                <div className={styles.contactMethods}>
                  <div className={styles.contactMethod}>
                    <div className={styles.contactIcon}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                        <polyline points="22,6 12,13 2,6"></polyline>
                      </svg>
                    </div>
                    <div className={styles.contactDetails}>
                      <h3 className={styles.contactMethodTitle}>电子邮件</h3>
                      <a href={`mailto:${siteConfig.contact.email}`} className={styles.contactLink}>
                        {siteConfig.contact.email}
                      </a>
                    </div>
                  </div>

                  <div className={styles.contactMethod}>
                    <div className={styles.contactIcon}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                      </svg>
                    </div>
                    <div className={styles.contactDetails}>
                      <h3 className={styles.contactMethodTitle}>GitHub</h3>
                      <a href={siteConfig.social.github.url} target="_blank" rel="noopener noreferrer" className={styles.contactLink}>
                        github.com/{siteConfig.social.github.username}
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <div className={styles.contactForm}>
                <h2 className={styles.formTitle}>联系前可以直接带上这些信息</h2>

                <div className={styles.contactCard}>
                  <p className={styles.contactCardIntro}>
                    这是一个纯静态站点，目前没有在线表单。你可以直接发邮件，简单说明下面几项，我会更快判断是否适合继续沟通。
                  </p>

                  <ul className={styles.contactChecklist}>
                    <li>项目类型：后台、小程序、官网、系统对接，还是现有项目接手</li>
                    <li>当前状态：从 0 开始，还是已有项目需要迭代 / 修复 / 重构</li>
                    <li>你最在意的问题：进度、稳定性、交付质量，还是后续维护成本</li>
                    <li>期望时间：是否有明确上线时间，或者先做评估和拆解</li>
                  </ul>

                  <div className={styles.contactActions}>
                    <a href={`mailto:${siteConfig.contact.email}`} className={styles.primaryAction}>
                      直接发邮件
                    </a>
                    <a
                      href={siteConfig.social.github.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.secondaryAction}
                    >
                      查看 GitHub
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
