import { Link } from 'react-router-dom';
import { Shell, Card } from '../components/Layout';

export default function Home() {
  return (
    <Shell>
      <div className="grid w-full gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card title="VoiceAid">
          <p className="max-w-xl">
            A simple voice-first legal assistant that helps people start conversations, review past
            interactions, and understand the support available to them.
          </p>
          <div className="mt-6">
            <Link
              to="/voice"
              className="inline-flex items-center rounded-full bg-cyan-400 px-5 py-3 font-medium text-slate-950 transition hover:bg-cyan-300"
            >
              Start Voice Assistant
            </Link>
          </div>
        </Card>

        <div className="grid gap-4">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-slate-300">
            Clean, mobile-friendly, and ready for the voice flow.
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-slate-300">
            Built with React Router and Tailwind CSS.
          </div>
        </div>
      </div>
    </Shell>
  );
}
