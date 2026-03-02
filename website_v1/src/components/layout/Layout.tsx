import { Outlet } from 'react-router-dom';
import { Footer } from './Footer';
import { Navbar } from './Navbar';

export function Layout() {
  return (
    <>
      <Navbar />
      <main className="container page-main">
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
