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

import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import siteConfig from '@/config/site';
import styles from '@/styles/Legal.module.css';

export default function Privacy() {
  return (
    <>
      <Head>
        <title>隐私政策 - {siteConfig.title}</title>
        <meta name="description" content="了解我们如何收集、使用和保护您的个人信息" />
        <meta name="robots" content="noindex" />
      </Head>
      <Layout>
        <div className={styles.legalPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>隐私政策</h1>

            <div className={styles.legalContent}>
              <p className={styles.lastUpdated}>最后更新日期：{new Date().getFullYear()}年{new Date().getMonth() + 1}月{new Date().getDate()}日</p>

              <section className={styles.section}>
                <h2>概述</h2>
                <p>
                  本隐私政策描述了我们在您使用本网站时如何收集、使用和保护您的个人信息。
                  我们重视您的隐私，并致力于保护您的个人数据。请仔细阅读本政策，以了解我们的做法。
                </p>
              </section>

              <section className={styles.section}>
                <h2>信息收集</h2>
                <p>我们可能收集的信息包括：</p>
                <ul>
                  <li>基本信息：当您通过联系表单与我们联系时，我们会收集您的姓名和电子邮件地址。</li>
                  <li>使用数据：我们可能会收集有关您如何使用我们网站的信息，包括访问时间、浏览页面和停留时间。</li>
                  <li>设备信息：我们可能会收集有关您使用的设备的信息，如IP地址、浏览器类型和操作系统。</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>信息使用</h2>
                <p>我们使用收集的信息：</p>
                <ul>
                  <li>回复您的咨询和请求</li>
                  <li>改进我们的网站和服务</li>
                  <li>分析网站使用情况和趋势</li>
                  <li>保护网站安全并防止欺诈活动</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>信息共享</h2>
                <p>
                  我们不会出售、出租或交易您的个人信息给第三方。在以下情况下，我们可能会共享您的信息：
                </p>
                <ul>
                  <li>经您同意</li>
                  <li>为遵守法律要求</li>
                  <li>保护我们的权利和财产</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>Cookie使用</h2>
                <p>
                  我们的网站可能使用Cookie和类似技术来增强您的浏览体验。这些技术帮助我们了解访问者如何使用我们的网站，
                  并允许某些功能，如保存您的主题偏好设置。
                </p>
                <p>
                  您可以通过浏览器设置控制Cookie的使用，但这可能会影响某些网站功能的可用性。
                </p>
              </section>

              <section className={styles.section}>
                <h2>数据安全</h2>
                <p>
                  我们采取合理的安全措施来保护您的个人信息不被未经授权的访问、使用或披露。
                  然而，请注意互联网传输不是完全安全的，我们不能保证通过网络传输的信息的绝对安全性。
                </p>
              </section>

              <section className={styles.section}>
                <h2>您的权利</h2>
                <p>根据适用的数据保护法律，您可能拥有以下权利：</p>
                <ul>
                  <li>访问您的个人数据</li>
                  <li>更正不准确的数据</li>
                  <li>要求删除您的数据</li>
                  <li>限制或反对处理您的数据</li>
                  <li>数据可携带性</li>
                </ul>
                <p>
                  如果您希望行使这些权利，请通过网站上提供的联系方式与我们联系。
                </p>
              </section>

              <section className={styles.section}>
                <h2>政策更新</h2>
                <p>
                  我们可能会不时更新本隐私政策。任何变更将在本页面上发布，并在重大变更时通过适当方式通知您。
                  我们鼓励您定期查看本政策以了解最新信息。
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
