export function PrivacyPage() {
  return (
    <section className="stack-md">
      <h1>隐私说明</h1>
      <p>本网站仅收集建立联系所需的最小信息，不用于与沟通无关的用途。</p>

      <article className="card">
        <h2>收集内容</h2>
        <ul>
          <li>姓名、邮箱、主题、消息内容。</li>
          <li>可选字段：电话或公司信息（若用户主动提供）。</li>
        </ul>
      </article>

      <article className="card">
        <h2>数据用途与保留</h2>
        <ul>
          <li>仅用于合作咨询与技术交流回复。</li>
          <li>默认保留 180 天，可按请求提前删除。</li>
          <li>删除请求渠道：联系页面提供的邮箱。</li>
        </ul>
      </article>

      <article className="card">
        <h2>第三方服务</h2>
        <ul>
          <li>表单托管：Formspree 或 EmailJS。</li>
          <li>统计服务：Google Analytics 或 Plausible（启用时会在站点声明）。</li>
          <li>评论服务：Giscus 或 Disqus（V2 启用）。</li>
        </ul>
      </article>
    </section>
  );
}
