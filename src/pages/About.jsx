import { Shell, Card } from '../components/Layout';

export default function About() {
  return (
    <Shell>
      <Card title="About VoiceAid">
        <div className="space-y-4">
          <p>
            VoiceAid is a voice-first legal assistant built to make legal help easier to access
            and understand.
          </p>
          <p>
            It is designed to help low-literacy users by turning spoken questions into clear,
            guided support.
          </p>
          <p>
            The app uses AI with memory so it can remember past interactions and provide more
            relevant responses over time.
          </p>
          <div className="pt-2">
            <h2 className="text-base font-semibold text-white">Tech Stack</h2>
            <ul className="mt-2 space-y-1">
              <li>Vapi for voice interaction</li>
              <li>Qdrant for memory storage</li>
              <li>FastAPI backend for API handling</li>
            </ul>
          </div>
        </div>
      </Card>
    </Shell>
  );
}
