import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { navLinks } from '../../data/site';

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="navbar-wrap">
      <div className="container navbar">
        <NavLink className="brand" to="/">
          Saber Dev
        </NavLink>
        <button
          className="menu-toggle"
          onClick={() => setOpen((prev) => !prev)}
          type="button"
        >
          菜单
        </button>
        <nav className={open ? 'nav-open' : ''}>
          <ul>
            {navLinks.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) => (isActive ? 'active' : '')}
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
