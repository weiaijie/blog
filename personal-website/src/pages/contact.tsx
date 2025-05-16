/**
 * contact.tsx
 *
 * 描述：联系页面，提供联系方式和消息发送表单
 *
 * 功能：
 * - 展示联系信息（电子邮件、GitHub、LinkedIn）
 * - 提供消息发送表单，包含姓名、电子邮件、主题和消息内容
 * - 表单提交状态管理（提交中、成功、错误）
 *
 * 主要组件：
 * - Contact：联系页面的主要组件
 * - 包含表单状态管理和提交逻辑
 */

import Head from 'next/head';
import { useState } from 'react';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/Contact.module.css';

export default function Contact() {
  // 表单状态
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  // 表单提交状态
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // 处理输入变化
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 处理表单提交
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError('');

    // 模拟表单提交
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitSuccess(true);

      // 重置表单
      setFormData({
        name: '',
        email: '',
        subject: '',
        message: ''
      });

      // 5秒后重置成功状态
      setTimeout(() => {
        setSubmitSuccess(false);
      }, 5000);
    }, 1500);
  };

  return (
    <>
      <Head>
        <title>联系 - saber的个人网站</title>
        <meta name="description" content="联系我，讨论项目合作或技术交流" />
      </Head>
      <Layout>
        <div className={styles.contactPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>联系我</h1>

            <div className={styles.contactContent}>
              <div className={styles.contactInfo}>
                <p className={styles.contactText}>
                  如果您有任何问题或合作意向，欢迎随时与我联系。我会尽快回复您的消息。
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
                      <a href="mailto:contact@example.com" className={styles.contactLink}>
                        contact@example.com
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
                      <a href="https://github.com/" target="_blank" rel="noopener noreferrer" className={styles.contactLink}>
                        github.com/username
                      </a>
                    </div>
                  </div>

                  <div className={styles.contactMethod}>
                    <div className={styles.contactIcon}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                        <rect x="2" y="9" width="4" height="12"></rect>
                        <circle cx="4" cy="4" r="2"></circle>
                      </svg>
                    </div>
                    <div className={styles.contactDetails}>
                      <h3 className={styles.contactMethodTitle}>LinkedIn</h3>
                      <a href="https://linkedin.com/" target="_blank" rel="noopener noreferrer" className={styles.contactLink}>
                        linkedin.com/in/username
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <div className={styles.contactForm}>
                <h2 className={styles.formTitle}>发送消息</h2>

                {submitSuccess ? (
                  <div className={styles.successMessage}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                      <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                    <p>消息已发送！我会尽快回复您。</p>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className={styles.form}>
                    <div className={styles.formGroup}>
                      <label htmlFor="name" className={styles.formLabel}>姓名</label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className={styles.formInput}
                        placeholder="请输入您的姓名"
                        required
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label htmlFor="email" className={styles.formLabel}>电子邮件</label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className={styles.formInput}
                        placeholder="请输入您的电子邮件"
                        required
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label htmlFor="subject" className={styles.formLabel}>主题</label>
                      <select
                        id="subject"
                        name="subject"
                        value={formData.subject}
                        onChange={handleChange}
                        className={styles.formSelect}
                        required
                      >
                        <option value="" disabled>请选择主题</option>
                        <option value="project">项目合作</option>
                        <option value="job">工作机会</option>
                        <option value="question">技术咨询</option>
                        <option value="other">其他</option>
                      </select>
                    </div>

                    <div className={styles.formGroup}>
                      <label htmlFor="message" className={styles.formLabel}>消息</label>
                      <textarea
                        id="message"
                        name="message"
                        value={formData.message}
                        onChange={handleChange}
                        className={styles.formTextarea}
                        placeholder="请输入您的消息"
                        rows={5}
                        required
                      ></textarea>
                    </div>

                    {submitError && (
                      <div className={styles.errorMessage}>{submitError}</div>
                    )}

                    <button
                      type="submit"
                      className={styles.submitButton}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? '发送中...' : '发送消息'}
                      {!isSubmitting && (
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.buttonIcon}>
                          <line x1="5" y1="12" x2="19" y2="12"></line>
                          <polyline points="12 5 19 12 12 19"></polyline>
                        </svg>
                      )}
                    </button>
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
