/**
 * about.tsx
 *
 * 描述：关于我页面，展示个人信息、技能和经历
 *
 * 功能：
 * - 展示个人基本信息和介绍
 * - 显示核心技能和专长
 * - 展示工作经历和教育背景
 * - 简约的苹果风格设计
 *
 * 主要组件：
 * - About：关于我页面主组件
 */

import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SEOHead from '@/components/common/SEOHead';
import useReducedMotion, { getReducedMotionVariants, getReducedMotionTransition } from '@/hooks/useReducedMotion';
import styles from '@/styles/About.module.css';

export default function About() {
  // 检测用户动画偏好
  const prefersReducedMotion = useReducedMotion();

  // 页面动画变体
  const pageVariants = getReducedMotionVariants({
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: getReducedMotionTransition({
        duration: 0.6,
        ease: "easeOut"
      }, prefersReducedMotion)
    }
  }, prefersReducedMotion);

  const titleVariants = getReducedMotionVariants({
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: getReducedMotionTransition({
        duration: 0.8,
        ease: "easeOut",
        delay: 0.2
      }, prefersReducedMotion)
    }
  }, prefersReducedMotion);

  return (
    <>
      <SEOHead
        title="关于我"
        description="7年全栈开发经验，Vue生态系统专家，专注前端技术，具备全栈开发能力"
        type="profile"
        keywords={['全栈开发', '前端开发', '后端开发', 'React', 'Vue.js', 'Next.js', 'Node.js', '许辉']}
        image="/images/about-og.jpg"
      />
      <Layout>
        <motion.div 
          className={styles.aboutPage}
          variants={pageVariants}
          initial="hidden"
          animate="visible"
        >
          <div className={styles.container}>
            <motion.h1 
              className={styles.pageTitle}
              variants={titleVariants}
              initial="hidden"
              animate="visible"
            >
              关于我
            </motion.h1>

            {/* 个人介绍 */}
            <motion.section
              className={styles.introSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              aria-label="个人介绍"
              role="region"
            >
              <div className={styles.introContent}>
                <p className={styles.introText}>
                  你好！我是许辉，一名专注于前端技术的全栈开发工程师，拥有7年丰富的项目开发经验。
                </p>
                <p className={styles.introText}>
                  我的技术栈以前端为核心，深度掌握Vue生态系统（Vue2/Vue3、Vuex/Pinia、Vue Router），
                  熟练运用TypeScript、JavaScript ES6+，精通Element-UI、Ant-Design等主流UI框架。
                  同时具备Node.js后端开发能力，能够独立完成全栈项目的架构设计和开发实现。
                </p>
                <p className={styles.introText}>
                  在移动端开发方面，我有丰富的UniApp跨平台开发经验，熟悉Vant、uView等移动端UI框架。
                  曾参与医疗SaaS、金融交易、建筑管理等多个行业的核心系统开发，
                  具备从0到1的项目架构能力和团队技术指导经验。
                </p>
                <p className={styles.introText}>
                  我注重代码质量和用户体验，擅长性能优化和组件设计，
                  曾通过技术优化将系统页面加载时间从4s提升至1s，团队开发效率提升40%以上。
                  期待在新的平台上继续发挥技术专长，创造更大的价值。
                </p>
              </div>
            </motion.section>

            {/* 核心技能 */}
            <motion.section
              className={styles.skillsSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              aria-labelledby="skills-heading"
              role="region"
            >
              <h2 id="skills-heading" className={styles.sectionTitle}>核心技能</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillCategory}>
                  <h3 className={styles.categoryTitle}>前端开发</h3>
                  <div className={styles.skillTags}>
                    <span className={styles.skillTag}>Vue2/Vue3</span>
                    <span className={styles.skillTag}>TypeScript</span>
                    <span className={styles.skillTag}>JavaScript</span>
                    <span className={styles.skillTag}>Element-UI</span>
                    <span className={styles.skillTag}>Ant-Design</span>
                    <span className={styles.skillTag}>Vant</span>
                    <span className={styles.skillTag}>UniApp</span>
                    <span className={styles.skillTag}>React</span>
                    <span className={styles.skillTag}>Next.js</span>
                  </div>
                </div>
                <div className={styles.skillCategory}>
                  <h3 className={styles.categoryTitle}>后端开发</h3>
                  <div className={styles.skillTags}>
                    <span className={styles.skillTag}>Node.js</span>
                    <span className={styles.skillTag}>Express</span>
                    <span className={styles.skillTag}>MySQL</span>
                    <span className={styles.skillTag}>Redis</span>
                    <span className={styles.skillTag}>ThinkPHP</span>
                  </div>
                </div>
                <div className={styles.skillCategory}>
                  <h3 className={styles.categoryTitle}>开发工具</h3>
                  <div className={styles.skillTags}>
                    <span className={styles.skillTag}>Git</span>
                    <span className={styles.skillTag}>Webpack</span>
                    <span className={styles.skillTag}>Vite</span>
                    <span className={styles.skillTag}>Linux</span>
                    <span className={styles.skillTag}>Nginx</span>
                    <span className={styles.skillTag}>ECharts</span>
                  </div>
                </div>
              </div>
            </motion.section>

            {/* 工作经历 */}
            <motion.section
              className={styles.experienceSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.8 }}
              aria-labelledby="experience-heading"
              role="region"
            >
              <h2 id="experience-heading" className={styles.sectionTitle}>工作经历</h2>
              <div className={styles.timeline}>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>前端开发工程师</h3>
                    <p className={styles.company}>上海墨安信息科技有限公司</p>
                    <p className={styles.period}>2022.06 - 2024.10</p>
                    <div className={styles.description}>
                      <p><strong>项目：</strong>医院教育管理SaaS系统 - 服务多家三甲医院的教育培训平台</p>
                      <p><strong>主要成就：</strong></p>
                      <ul>
                        <li>负责用户管理、档案管理、评价系统等核心模块的前端开发</li>
                        <li>创新设计动态表单引擎，通过JSON配置生成复杂表单，提升开发效率40%</li>
                        <li>开发Node.js中间层工具，解决前后端分离调试问题，优化开发流程</li>
                        <li>指导2-3名新人开发，建立技术分享机制，提升团队整体技术水平</li>
                        <li>实施性能优化，通过懒加载等技术将页面加载速度提升30%</li>
                      </ul>
                      <p><strong>技术栈：</strong>Vue2/Vue3、Element-UI、TypeScript、Node.js</p>
                    </div>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>全栈开发工程师</h3>
                    <p className={styles.company}>上海饰百秀网络科技有限公司</p>
                    <p className={styles.period}>2021.09 - 2022.05</p>
                    <div className={styles.description}>
                      <p><strong>项目：</strong>建筑装修项目管理系统 - 独立全栈开发</p>
                      <p><strong>主要成就：</strong></p>
                      <ul>
                        <li>独立完成系统架构设计，包括数据库设计、API设计和前端架构</li>
                        <li>开发PC端后台（Vue3 + Ant-Design）和移动端（UniApp + uView）</li>
                        <li>实现Excel批量导入，支持三层关系任务数据的智能解析</li>
                        <li>开发甘特图组件，支持拖拽调整和实时进度更新</li>
                        <li>移动端应用提升现场作业效率50%，获得客户高度认可</li>
                      </ul>
                      <p><strong>技术栈：</strong>Vue3、Ant-Design、UniApp、Node.js、Express、MySQL</p>
                    </div>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>全栈开发工程师</h3>
                    <p className={styles.company}>上海国芮信息科技有限公司</p>
                    <p className={styles.period}>2019.10 - 2021.06</p>
                    <div className={styles.description}>
                      <p><strong>项目：</strong>数字货币交易平台后台管理系统 - 支撑5-6万用户</p>
                      <p><strong>主要成就：</strong></p>
                      <ul>
                        <li>设计多层级权限控制系统，支持10+角色、50+权限灵活组合</li>
                        <li>开发用户管理、营销活动、理财系统等核心业务模块</li>
                        <li>使用ECharts构建数据可视化大屏，实时展示关键业务指标</li>
                        <li>建立系统监控预警机制，保障平台稳定运行</li>
                        <li>性能优化：页面加载从4s优化到1s，接口响应提升60%</li>
                      </ul>
                      <p><strong>技术栈：</strong>Vue2、Element-UI、ECharts、Node.js、Express、MySQL、Redis</p>
                    </div>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>Web开发工程师</h3>
                    <p className={styles.company}>上海欧莱美医疗美容医院有限公司</p>
                    <p className={styles.period}>2018.05 - 2019.08</p>
                    <div className={styles.description}>
                      <p><strong>项目：</strong>医疗美容官网和商品展示系统 - 职业起步项目</p>
                      <p><strong>主要成就：</strong></p>
                      <ul>
                        <li>独立完成医院官网开发，包括响应式设计和交互效果</li>
                        <li>开发医美商品展示系统，实现分类、搜索、详情等功能</li>
                        <li>基于ThinkPHP构建后台管理系统，支持内容管理</li>
                        <li>严格遵循医疗行业规范，确保网站内容合规性</li>
                        <li>建立完整的Web开发技能体系，为全栈发展奠定基础</li>
                      </ul>
                      <p><strong>技术栈：</strong>JavaScript、Vue、HTML/CSS、ThinkPHP、MySQL</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.section>

            {/* 教育背景 */}
            <motion.section
              className={styles.educationSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 1.0 }}
              aria-labelledby="education-heading"
              role="region"
            >
              <h2 id="education-heading" className={styles.sectionTitle}>教育背景</h2>
              <div className={styles.educationCard}>
                <h3 className={styles.degree}>大专 · 计算机应用技术</h3>
                <p className={styles.school}>上海中侨职业技术学院</p>
                <p className={styles.period}>2015.09 - 2018.06</p>
              </div>
            </motion.section>
          </div>
        </motion.div>
      </Layout>
    </>
  );
}
