import { Link } from 'react-router-dom';
import { useMemo, useState } from 'react';
import { Card } from '../components/common/Card';
import { featuredProjects } from '../data/site';

export function ProjectsPage() {
  const [typeFilter, setTypeFilter] = useState('全部');
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'stack'>('date');

  const types = useMemo(
    () => ['全部', ...new Set(featuredProjects.map((project) => project.type))],
    []
  );

  const visibleProjects = useMemo(() => {
    const filtered =
      typeFilter === '全部'
        ? featuredProjects
        : featuredProjects.filter((project) => project.type === typeFilter);

    const sorted = [...filtered].sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      }
      if (sortBy === 'stack') {
        return a.stack.localeCompare(b.stack);
      }
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    });

    return sorted;
  }, [sortBy, typeFilter]);

  return (
    <section className="stack-md">
      <h1>项目</h1>
      <p>V1 展示核心项目，并提供基础筛选与排序能力。</p>
      <div className="toolbar">
        <label className="field">
          <span>分类</span>
          <select
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value)}
          >
            {types.map((type) => (
              <option value={type} key={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>排序</span>
          <select
            value={sortBy}
            onChange={(event) =>
              setSortBy(
                event.target.value === 'name'
                  ? 'name'
                  : event.target.value === 'stack'
                    ? 'stack'
                    : 'date'
              )
            }
          >
            <option value="date">按日期</option>
            <option value="name">按名称</option>
            <option value="stack">按技术栈</option>
          </select>
        </label>
      </div>
      <div className="grid-3">
        {visibleProjects.length === 0 && (
          <article className="card">
            <h3>暂无匹配项目</h3>
            <p>请切换筛选条件查看其它项目。</p>
          </article>
        )}
        {visibleProjects.map((project) => {
          const meta = `${project.type} / ${project.stack} / ${project.date}`;
          return (
            <Card key={project.name} title={project.name}>
              {project.summary}（{meta}）
              <span className="card-action">
                <Link to={`/projects/${project.slug}`}>查看项目详情</Link>
              </span>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
