import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { FormField } from '../components/common/FormField';

export function ContactPage() {
  const formEndpoint = import.meta.env.VITE_FORMSPREE_ENDPOINT;
  const [statusText, setStatusText] = useState('');
  const [statusType, setStatusType] = useState<'success' | 'error' | ''>('');
  const [submitting, setSubmitting] = useState(false);

  const onSubmitGuard = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!formEndpoint) {
      setStatusText('未配置表单服务，请先设置 VITE_FORMSPREE_ENDPOINT。');
      setStatusType('error');
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);

    if (String(formData.get('_gotcha') ?? '').trim()) {
      setStatusText('提交失败，请稍后重试。');
      setStatusType('error');
      return;
    }

    setSubmitting(true);
    setStatusText('');
    setStatusType('');
    try {
      const response = await fetch(formEndpoint, {
        method: 'POST',
        body: formData,
        headers: {
          Accept: 'application/json'
        }
      });
      if (!response.ok) {
        throw new Error('request_failed');
      }
      form.reset();
      setStatusText('提交成功，已收到你的消息。');
      setStatusType('success');
    } catch {
      setStatusText('提交失败，请检查网络或稍后重试。');
      setStatusType('error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="stack-md">
      <h1>联系方式</h1>
      <p>欢迎通过表单或邮箱联系我。V1 使用托管表单服务接收消息。</p>
      <p className="note">时区：UTC+8，工作日通常 24-48 小时内回复。</p>
      <section>
        <h2>联系渠道</h2>
        <ul>
          <li>邮箱：contact@example.com</li>
          <li>GitHub：用于项目与代码协作沟通。</li>
          <li>LinkedIn：用于职业合作与机会交流。</li>
        </ul>
      </section>

      <form className="contact-form" method="POST" onSubmit={onSubmitGuard}>
        <FormField label="姓名" name="name" required />
        <FormField label="邮箱" name="email" type="email" required />
        <input className="honeypot" name="_gotcha" tabIndex={-1} autoComplete="off" />
        <label className="field">
          <span>主题</span>
          <select name="topic" required>
            <option value="">请选择主题</option>
            <option value="project">项目合作</option>
            <option value="job">工作机会</option>
            <option value="tech">技术交流</option>
          </select>
        </label>
        <label className="field">
          <span>内容</span>
          <textarea name="message" required rows={6} />
        </label>
        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? '发送中...' : '发送消息'}
        </button>
      </form>

      <p className="note">
        隐私说明：仅用于联系沟通，默认 180 天内清理历史记录。查看
        <Link to="/privacy">隐私说明</Link>。
      </p>
      {statusText && (
        <p className={statusType === 'success' ? 'status-ok' : 'warn'}>{statusText}</p>
      )}

      <section>
        <h2>常见问题</h2>
        <ul>
          <li>合作范围：个人网站、前端工程化、文档流程优化。</li>
          <li>合作流程：沟通需求 - 方案确认 - 分阶段交付 - 复盘优化。</li>
          <li>响应承诺：工作日 24-48 小时内回复，节假日顺延。</li>
        </ul>
      </section>
    </section>
  );
}
