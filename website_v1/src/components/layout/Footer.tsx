import { Link } from 'react-router-dom';

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="footer-wrap">
      <div className="container footer">
        <div>
          <p>GitHub / LinkedIn / X</p>
          <p>contact@example.com</p>
          <p>
            <Link to="/privacy">隐私说明</Link>
          </p>
        </div>
        <p>© {year} Saber Dev. Built with React + TypeScript + Vite.</p>
      </div>
    </footer>
  );
}
