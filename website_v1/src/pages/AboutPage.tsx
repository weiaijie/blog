import { aboutTimeline, valuePrinciples } from '../data/site';

export function AboutPage() {
  return (
    <section className="stack-md">
      <h1>关于我</h1>
      <p>
        我是一名偏工程化方向的开发者，关注从需求拆解、实现到发布的完整交付链路。当前聚焦 React 生态、前端性能和部署自动化。
      </p>

      <section>
        <h2>成长与经历时间线</h2>
        <div className="timeline">
          {aboutTimeline.map((item) => (
            <article key={item.year} className="timeline-item">
              <p className="timeline-year">{item.year}</p>
              <h3>{item.title}</h3>
              <p>{item.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>价值观与方法</h2>
        <div className="grid-3">
          {valuePrinciples.map((item) => (
            <article key={item.name} className="card">
              <h3>{item.name}</h3>
              <p>{item.example}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>兴趣与学习</h2>
        <ul>
          <li>持续跟踪前端工程化工具链与最佳实践。</li>
          <li>
            技术相关业余项目：
            <a className="inline-link" href="#" target="_blank" rel="noreferrer">
              文档流程工具
            </a>
            、
            <a className="inline-link" href="#" target="_blank" rel="noreferrer">
              监控面板原型
            </a>
            。
          </li>
          <li>社区参与：持续关注技术社区讨论并进行实践复盘。</li>
          <li>当前学习重点（2026 Q2）：性能预算、前端可观测性与自动化质量门禁。</li>
        </ul>
      </section>
    </section>
  );
}
