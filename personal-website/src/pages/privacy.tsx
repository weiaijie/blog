/**
 * privacy.tsx
 *
 * 描述：隐私政策页面，详细说明网站的数据收集和使用政策
 *
 * 功能：
 * - 展示网站的隐私政策内容
 * - 说明数据收集、使用、存储和保护的相关政策
 * - 提供清晰的隐私条款结构
 *
 * 主要组件：
 * - Privacy：隐私政策页面的主要组件
 */

import Layout from '@/components/layout/Layout';
import SeoHead from '@/components/common/SeoHead';
import siteConfig from '@/config/site';
import styles from '@/styles/Legal.module.css';

export default function Privacy() {
  return (
    <>
      <SeoHead
        title="隐私政策 - 许辉"
        description="说明许辉个人网站会保存哪些基础访问信息，以及通过邮件联系时信息如何被使用。"
        path="/privacy/"
        noindex
      />
      <Layout>
        <div className={styles.legalPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>隐私政策</h1>

            <div className={styles.legalContent}>
              <p className={styles.lastUpdated}>最后更新日期：{new Date().getFullYear()}年{new Date().getMonth() + 1}月{new Date().getDate()}日</p>

              <section className={styles.section}>
                <h2>概述</h2>
                <p>
                  本网站是许辉的个人展示站，采用静态方式部署。这里不会提供账号注册、在线下单或站内留言系统，
                  因此本页主要说明浏览访问和邮件联系两种场景下可能涉及的信息。
                </p>
              </section>

              <section className={styles.section}>
                <h2>信息收集</h2>
                <p>当前可能涉及的信息主要包括：</p>
                <ul>
                  <li>访问日志：站点托管平台可能会记录基础访问日志，例如访问时间、请求路径、IP、浏览器和设备信息。</li>
                  <li>主题偏好：网站会在浏览器本地保存主题模式设置，用于记住亮色或暗色偏好。</li>
                  <li>主动联系信息：如果您通过电子邮件联系我，邮件中提供的姓名、联系方式和项目说明会出现在对应的邮箱服务中。</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>信息使用</h2>
                <p>这些信息仅会用于：</p>
                <ul>
                  <li>维持站点基本可用性和访问安全</li>
                  <li>记住主题模式等本地浏览偏好</li>
                  <li>在您主动来信时回复咨询、沟通合作或说明项目情况</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>信息共享</h2>
                <p>
                  我不会主动出售或转让您的个人信息。访问过程中涉及的数据可能由托管服务商、CDN 或邮箱服务商按其基础设施流程处理，
                  但不会被我额外用于无关用途。
                </p>
              </section>

              <section className={styles.section}>
                <h2>Cookie使用</h2>
                <p>
                  当前网站不会接入广告、埋点或营销型 Cookie。浏览器本地可能只会保存主题模式等最小必要偏好，
                  用于改善阅读体验。
                </p>
                <p>
                  您可以通过浏览器设置清除这些本地数据，但这可能导致主题偏好失效。
                </p>
              </section>

              <section className={styles.section}>
                <h2>数据安全</h2>
                <p>
                  我会尽量减少不必要的数据收集，并依赖托管平台和邮箱服务的基础安全能力。但任何网络传输都无法保证绝对安全，
                  因此如果您需要发送敏感资料，建议先通过邮件确认沟通方式。
                </p>
              </section>

              <section className={styles.section}>
                <h2>您的权利</h2>
                <p>如果您曾主动通过邮件联系，并希望我删除相关沟通信息，可以直接来信说明：</p>
                <ul>
                  <li>您发送过的大致时间</li>
                  <li>使用的联系邮箱</li>
                  <li>希望处理的内容范围</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>政策更新</h2>
                <p>
                  如果站点能力或数据处理方式发生明显变化，我会在本页更新说明。
                </p>
              </section>

              <section className={styles.section}>
                <h2>联系我们</h2>
                <p>
                  如果您对本隐私政策有任何疑问或顾虑，请通过以下方式联系我们：
                </p>
                <p>
                  电子邮件：{siteConfig.contact.email}
                </p>
              </section>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
