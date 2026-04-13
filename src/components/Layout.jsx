import { Link, NavLink } from 'react-router-dom';

const navLinkClass = ({ isActive }) =>
  [
    'rounded-full px-3 py-2 text-sm font-medium transition',
    isActive ? 'bg-slate-100 text-slate-950' : 'text-slate-300 hover:bg-white/10 hover:text-white',
  ].join(' ');

export function Shell({ children }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.18),_transparent_40%),linear-gradient(180deg,#020617_0%,#0f172a_100%)]">
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="text-lg font-semibold tracking-tight text-white">
          VoiceAid
        </Link>
        <nav className="flex items-center gap-2">
          <NavLink to="/" className={navLinkClass} end>
            Home
          </NavLink>
          <NavLink to="/voice" className={navLinkClass}>
            Voice
          </NavLink>
          <NavLink to="/history" className={navLinkClass}>
            History
          </NavLink>
          <NavLink to="/about" className={navLinkClass}>
            About
          </NavLink>
        </nav>
      </header>
      <main className="mx-auto flex w-full max-w-5xl items-center px-4 pb-12 pt-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}

export function Card({ title, children }) {
  return (
    <div className="w-full rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-slate-950/30 backdrop-blur sm:p-8">
      <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{title}</h1>
      <div className="mt-4 text-sm leading-6 text-slate-300 sm:text-base">{children}</div>
    </div>
  );
}
