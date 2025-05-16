/**
 * terms.tsx
 *
 * 描述：使用条款页面，详细说明网站的使用规则和条件
 *
 * 功能：
 * - 展示网站的使用条款内容
 * - 说明用户权利和责任
 * - 提供知识产权、免责声明等法律信息
 *
 * 主要组件：
 * - Terms：使用条款页面的主要组件
 */

import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import siteConfig from '@/config/site';
import styles from '@/styles/Legal.module.css';

export default function Terms() {
  return (
    <>
      <Head>
        <title>使用条款 - {siteConfig.title}</title>
        <meta name="description" content="了解使用本网站的条款和条件" />
        <meta name="robots" content="noindex" />
      </Head>
      <Layout>
        <div className={styles.legalPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>使用条款</h1>

            <div className={styles.legalContent}>
              <p className={styles.lastUpdated}>最后更新日期：{new Date().getFullYear()}年{new Date().getMonth() + 1}月{new Date().getDate()}日</p>

              <section className={styles.section}>
                <h2>接受条款</h2>
                <p>
                  欢迎访问{siteConfig.author}的个人网站。通过访问和使用本网站，您同意接受并遵守这些条款和条件。
                  如果您不同意这些条款的任何部分，请不要使用本网站。
                </p>
              </section>

              <section className={styles.section}>
                <h2>使用许可</h2>
                <p>
                  在遵守这些使用条款的前提下，我们授予您访问和个人使用本网站的有限许可。此许可不包括：
                </p>
                <ul>
                  <li>本网站或其内容的商业使用</li>
                  <li>对本网站或其内容的修改或复制</li>
                  <li>尝试反编译或逆向工程网站的任何部分</li>
                  <li>移除网站上的版权或其他所有权声明</li>
                  <li>将网站内容用于任何公共展示或商业目的</li>
                </ul>
                <p>
                  违反这些条款将导致此许可的自动终止，我们可能会采取适当的法律行动。
                </p>
              </section>

              <section className={styles.section}>
                <h2>内容和版权</h2>
                <p>
                  本网站上的所有内容，包括但不限于文本、图像、图形、代码、设计和整体布局，均为我的财产或已获得使用许可。
                  这些内容受版权法和其他知识产权法保护。
                </p>
                <p>
                  您可以查看和下载本网站的内容，仅供个人、非商业用途，前提是您保留所有版权和其他所有权声明。
                </p>
              </section>

              <section className={styles.section}>
                <h2>用户行为</h2>
                <p>使用本网站时，您同意不会：</p>
                <ul>
                  <li>违反任何适用的法律或法规</li>
                  <li>侵犯他人的知识产权或其他权利</li>
                  <li>传播恶意软件或有害代码</li>
                  <li>尝试未经授权访问网站的任何部分</li>
                  <li>干扰或破坏网站的正常运行</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>外部链接</h2>
                <p>
                  本网站可能包含指向第三方网站的链接。这些链接仅为方便用户而提供，不构成对这些网站或其内容的认可。
                  我们对这些外部网站的内容、隐私政策或做法不负任何责任。
                </p>
              </section>

              <section className={styles.section}>
                <h2>免责声明</h2>
                <p>
                  本网站及其内容按"原样"提供，不提供任何明示或暗示的保证。在法律允许的最大范围内，我们不对网站的可用性、
                  可靠性或准确性，或因使用本网站而产生的任何直接、间接、附带、特殊或后果性损害承担责任。
                </p>
              </section>

              <section className={styles.section}>
                <h2>赔偿</h2>
                <p>
                  您同意赔偿并使我们免受因您违反这些使用条款或您使用本网站而产生的任何索赔、损失、责任、费用和开支的影响。
                </p>
              </section>

              <section className={styles.section}>
                <h2>条款修改</h2>
                <p>
                  我们保留随时修改这些使用条款的权利。修改后的条款将在本页面上发布，并在发布后立即生效。
                  继续使用本网站将被视为接受修改后的条款。
                </p>
              </section>

              <section className={styles.section}>
                <h2>适用法律</h2>
                <p>
                  这些使用条款受中国法律管辖，并按其解释，不考虑法律冲突原则。
                </p>
              </section>

              <section className={styles.section}>
                <h2>联系我们</h2>
                <p>
                  如果您对这些使用条款有任何疑问或意见，请通过以下方式联系我们：
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
