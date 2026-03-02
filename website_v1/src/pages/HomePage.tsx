import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { coreSkills, featuredProjects } from '../data/site';

export function HomePage() {
  return (
    <section className="stack-lg">
      <section className="hero">
        <p className="eyebrow">个人网站 V1</p>
        <h1>构建稳定、可维护、可持续迭代的个人品牌站点</h1>
        <p>
          我专注于前端工程化和产品交付，把复杂需求拆解成可执行任务并持续推进落地。
        </p>
        <div className="hero-actions">
          <Button to="/about">了解更多</Button>
          <Button to="/projects">查看项目</Button>
        </div>
      </section>

      <section>
        <h2>技能亮点</h2>
        <div className="grid-2">
          {coreSkills.map((skill) => (
            <Card key={skill.name} title={`${skill.name} · ${skill.level}`}>
              {skill.desc}
            </Card>
          ))}
        </div>
        <div className="section-action">
          <Button to="/skills">查看全部技能</Button>
        </div>
      </section>

      <section>
        <h2>精选项目</h2>
        <div className="grid-3">
          {featuredProjects.map((project) => (
            <Card key={project.name} title={project.name}>
              {project.summary}
            </Card>
          ))}
        </div>
        <div className="section-action">
          <Button to="/projects">查看更多项目</Button>
        </div>
      </section>

      <section>
        <h2>最新动态（V1静态）</h2>
        <ul className="updates">
          <li>2026-03-01：完成网站执行计划与模块拆解。</li>
          <li>2026-03-01：启动 V1 工程脚手架与页面骨架开发。</li>
          <li>2026-03-01：落地基础路由、组件与样式系统第一版。</li>
        </ul>
      </section>
    </section>
  );
}
