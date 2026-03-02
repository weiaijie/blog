import { Link } from 'react-router-dom';
import type { ReactNode } from 'react';

type ButtonProps = {
  to: string;
  children: ReactNode;
};

export function Button({ to, children }: ButtonProps) {
  return (
    <Link className="btn-primary" to={to}>
      {children}
    </Link>
  );
}
