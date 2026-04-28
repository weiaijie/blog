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

import Layout from '@/components/layout/Layout';
import SeoHead from '@/components/common/SeoHead';
import siteConfig from '@/config/site';
import styles from '@/styles/Legal.module.css';

export default function Terms() {
  return (
    <>
      <SeoHead
        title="使用条款 - 许辉"
        description="说明访问许辉个人网站时适用的基础使用规则、内容版权和免责声明。"
        path="/terms/"
        noindex
      />
      <Layout>
        <div className={styles.legalPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>使用条款</h1>

            <div className={styles.legalContent}>
              <p className={styles.lastUpdated}>最后更新日期：{new Date().getFullYear()}年{new Date().getMonth() + 1}月{new Date().getDate()}日</p>

              <section className={styles.section}>
                <h2>接受条款</h2>
                <p>
                  欢迎访问{siteConfig.author}的个人网站。继续浏览本网站，即表示您理解本网站主要用于展示项目经历、
                  技术能力和公开联系方式，并同意在合法、合理的前提下使用这里的内容。
                </p>
              </section>

              <section className={styles.section}>
                <h2>使用许可</h2>
                <p>
                  您可以正常浏览、分享和引用本网站中的公开内容，但不应将其用于误导性用途。以下行为不被允许：
                </p>
                <ul>
                  <li>冒用本站内容、项目经历或身份信息</li>
                  <li>在未经说明来源的情况下大段复制页面内容用于商业宣传</li>
                  <li>恶意抓取、攻击或干扰网站的正常访问</li>
                  <li>将站内示例、文章或代码片段包装成您自己的原创成果</li>
                </ul>
              </section>

              <section className={styles.section}>
                <h2>内容和版权</h2>
                <p>
                  本网站上的所有内容，包括但不限于文本、图像、图形、代码、设计和整体布局，均为我的财产或已获得使用许可。
                  这些内容受版权法和其他知识产权法保护。
                </p>
                <p>
                  如需转载、二次发布或用于对外材料，建议先通过邮件沟通确认。
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
                  本网站可能包含指向第三方网站的链接，例如 GitHub 或其他外部资源。这些链接仅作为补充说明或作品展示入口，
                  我无法控制第三方站点后续的内容与政策变化。
                </p>
              </section>

              <section className={styles.section}>
                <h2>免责声明</h2>
                <p>
                  本网站内容会尽量保持真实和及时，但不承诺所有信息在任何时间点都完全准确或持续有效。
                  站内案例、文章和说明主要用于展示思路与经验，不构成正式商业承诺或法律、财务建议。
                </p>
              </section>

              <section className={styles.section}>
                <h2>联系与合作说明</h2>
                <p>
                  联系页展示的是公开联系方式，不代表任何需求都会承接，也不代表来信后一定形成合作。
                  是否继续推进，会根据项目类型、时间安排和沟通结果综合判断。
                </p>
              </section>

              <section className={styles.section}>
                <h2>条款修改</h2>
                <p>
                  如果网站结构、内容使用方式或联系方式发生明显变化，我可能会同步更新本页说明。
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
