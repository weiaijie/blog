import { Link, useParams } from 'react-router-dom';
import { featuredProjects } from '../data/site';

export function ProjectDetailPage() {
  const { slug } = useParams();
  const project = featuredProjects.find((item) => item.slug === slug);
  const related = featuredProjects
    .filter((item) => item.slug !== slug && item.type === project?.type)
    .slice(0, 2);

  if (!project) {
    return (
      <section className="stack-md">
        <h1>项目不存在</h1>
        <p>没有找到对应的项目详情，请返回项目列表查看。</p>
        <Link className="btn-primary" to="/projects">
          返回项目列表
        </Link>
      </section>
    );
  }

  return (
    <section className="stack-md">
      <p className="eyebrow-dark">{project.type}</p>
      <h1>{project.name}</h1>
      <p>{project.summary}</p>

      <article className="card">
        <h2>项目概述</h2>
        {project.overview.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}
      </article>

      <article className="card">
        <h2>模块架构</h2>
        <ul>
          {project.architecture.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>

      <div className="detail-meta">
        <article className="card">
          <h3>基本信息</h3>
          <p>角色：{project.role}</p>
          <p>周期：{project.duration}</p>
          <p>
            状态：<span className="tag">{project.status}</span>
          </p>
          <p>时间：{project.date}</p>
        </article>
        <article className="card">
          <h3>技术与方向</h3>
          <p>技术栈：{project.stack}</p>
          <p>项目类型：{project.type}</p>
        </article>
      </div>

      <article className="card">
        <h2>挑战与解决方案</h2>
        <p>
          <strong>挑战：</strong>
          {project.challenge}
        </p>
        <p>
          <strong>方案：</strong>
          {project.solution}
        </p>
        <p>
          <strong>取舍：</strong>
          {project.tradeoff}
        </p>
      </article>

      <article className="card">
        <h2>成果与影响</h2>
        <p>{project.impact}</p>
        <ul>
          {project.metrics.map((metric) => (
            <li key={metric}>{metric}</li>
          ))}
        </ul>
      </article>

      <article className="card">
        <h2>复盘</h2>
        <p>{project.retrospective}</p>
      </article>

      <article className="card">
        <h2>项目资源</h2>
        <ul>
          <li>在线演示：{project.links.demo ?? '待补充'}</li>
          <li>代码仓库：{project.links.repo ?? '待补充'}</li>
          <li>相关文档：{project.links.doc ?? '待补充'}</li>
        </ul>
      </article>

      {related.length > 0 && (
        <article className="card">
          <h2>相关项目推荐</h2>
          <ul>
            {related.map((item) => (
              <li key={item.slug}>
                <Link to={`/projects/${item.slug}`}>{item.name}</Link>
              </li>
            ))}
          </ul>
        </article>
      )}

      <Link className="btn-primary" to="/projects">
        返回项目列表
      </Link>
    </section>
  );
}
