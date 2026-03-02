import {
  backendSkillDetails,
  engineeringSkillDetails,
  skillMatrix,
  softSkillCases
} from '../data/site';

export function SkillsPage() {
  return (
    <section className="stack-md">
      <h1>技能</h1>

      {skillMatrix.map((group) => (
        <section key={group.group} className="stack-sm">
          <h2>{group.group}</h2>
          <div className="skills-grid">
            {group.items.map((skill) => (
              <article key={skill.name} className="skill-card">
                <div className="skill-head">
                  <h3>{skill.name}</h3>
                  <span className="tag">{skill.level}</span>
                </div>
                <p className="muted">最近使用：{skill.recent}</p>
                <p>证据：{skill.evidence}</p>
              </article>
            ))}
          </div>
        </section>
      ))}

      <section className="stack-sm">
        <h2>后端技能补充</h2>
        <ul>
          {backendSkillDetails.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="stack-sm">
        <h2>工程化与协作</h2>
        <ul>
          {engineeringSkillDetails.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="stack-sm">
        <h2>软技能案例</h2>
        <div className="grid-2">
          {softSkillCases.map((item) => (
            <article key={item.title} className="card">
              <h3>{item.title}</h3>
              <p>{item.case}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
