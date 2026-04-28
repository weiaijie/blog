/**
 * skills.tsx
 *
 * 描述：技能展示页面，用于展示个人的技术技能和专业能力
 *
 * 功能：
 * - 展示不同类别的技能（前端开发、后端开发、其他技术技能）
 * - 使用动画效果展示技能熟练度条
 * - 通过 IntersectionObserver 实现滚动时的技能条动画
 *
 * 主要组件：
 * - Skills：主要组件，包含技能展示逻辑和布局
 */

import { useEffect, useRef } from 'react';
import Layout from '@/components/layout/Layout';
import SeoHead from '@/components/common/SeoHead';
import styles from '@/styles/Skills.module.css';

export default function Skills() {
  const skillsRef = useRef<HTMLDivElement>(null);

  // 监听滚动，添加技能条动画
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.animate);
          }
        });
      },
      { threshold: 0.1 }
    );

    const skillBars = document.querySelectorAll(`.${styles.skillBar}`);
    skillBars.forEach((bar) => observer.observe(bar));

    return () => {
      skillBars.forEach((bar) => observer.unobserve(bar));
    };
  }, []);

  return (
    <>
      <SeoHead
        title="技能 - 许辉"
        description="查看许辉在前端、后端、业务系统设计和工程协作方面的技术能力与项目经验。"
        path="/skills/"
      />
      <Layout>
        <div className={styles.skillsPage} ref={skillsRef}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>技能</h1>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>前端与跨端</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>Vue / UniApp</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '92%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    长期使用 Vue2、Vue3 和 UniApp 交付后台系统与小程序项目，
                    熟悉组件拆分、状态流转、表单交互和多端页面组织方式。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>JavaScript/TypeScript</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '88%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    熟悉 ES6+、TypeScript、异步流程、接口封装和工程化开发，
                    能独立完成中后台和跨端项目的前端实现。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>React / Next.js</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '72%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    能使用 React 和 Next.js 搭建个人站、内容页和展示型项目，
                    也能在现有项目中完成组件开发和页面重构。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>后台 UI 与可视化</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '82%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    熟悉 Element UI、Ant Design、uView、ECharts，
                    做过后台管理系统、运营后台和数据看板类页面。
                  </p>
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>后端开发</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>PHP / ThinkPHP</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '78%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    做过基于 PHP、ThinkPHP、CRMEB 的企业项目和二次开发，
                    参与过后台系统、数据同步、商城改造和业务链路实现。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>Node.js / Express</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '76%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    能使用 Node.js 和 Express 完成接口、中间层和调试工具开发，
                    主要用在接口补充、联调辅助和问题排查这类场景。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>MySQL / Redis</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '80%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    做过表结构设计、业务字段扩展、查询优化、缓存使用和数据同步相关处理，
                    也会配合接口和日志一起查数据问题。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>业务系统设计</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '78%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    参与过权限、动态表单、数据同步、组合支付、运营后台等模块，
                    写功能时会顺手考虑后面怎么查问题、怎么继续改。
                  </p>
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>工程化与协作</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>版本控制</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '95%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    熟悉 Git 工作流、分支管理、代码评审和多人协作开发，
                    在已有项目里主要做功能迭代、问题修复和代码合并。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>部署与运行环境</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '68%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    接触过 Linux、Nginx、基础部署流程和线上问题排查，
                    能配合完成项目上线、环境配置和简单运维支持。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>团队协作</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '82%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    做过技术规范、需求拆解、联调沟通和新人带教，
                    也习惯把容易反复出错的地方整理成固定做法。
                  </p>
                </div>
              </div>
            </section>
          </div>
        </div>
      </Layout>
    </>
  );
}
