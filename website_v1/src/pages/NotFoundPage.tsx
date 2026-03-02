import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="stack-md">
      <h1>页面不存在</h1>
      <p>你访问的页面路径无效。</p>
      <Link to="/" className="btn-primary">
        返回首页
      </Link>
    </section>
  );
}
