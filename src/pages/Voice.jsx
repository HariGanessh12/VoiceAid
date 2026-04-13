import { useEffect, useRef, useState } from 'react';
import { Shell, Card } from '../components/Layout';
import { apiUrl } from '../lib/api';

export default function Voice() {
  const recognitionRef = useRef(null);
  const transcriptRef = useRef('');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('Idle');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');
  const [supported, setSupported] = useState(true);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => {
      setStatus('Listening...');
      setError('');
    };

    recognition.onresult = (event) => {
      transcriptRef.current = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join('')
        .trim();
    };

    recognition.onerror = () => {
      setStatus('Idle');
      setIsListening(false);
      setError('Speech recognition is not available in this browser.');
    };

    recognition.onend = async () => {
      setIsListening(false);
      setIsProcessing(true);

      const userMessage = transcriptRef.current.trim();
      if (!userMessage) {
        setStatus('Idle');
        setIsProcessing(false);
        return;
      }

      setMessages((current) => [...current, { role: 'user', text: userMessage }]);
      setStatus('Processing...');

      try {
        const response = await fetch(apiUrl('/voice-webhook'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: userMessage,
            call: { from: 'demo_user' },
          }),
        });

        if (!response.ok) {
          throw new Error('Request failed');
        }

        const data = await response.json();
        const aiText =
          typeof data === 'string'
            ? data
            : data?.message || data?.text || data?.response || data?.reply || 'No response returned.';

        setMessages((current) => [...current, { role: 'ai', text: aiText }]);
      } catch {
        setMessages((current) => [
          ...current,
          { role: 'ai', text: 'Unable to reach the backend right now.' },
        ]);
      } finally {
        transcriptRef.current = '';
        setStatus('Idle');
        setIsProcessing(false);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, []);

  const toggleListening = () => {
    setError('');

    if (isProcessing) {
      return;
    }

    if (!supported || !recognitionRef.current) {
      setError('Speech recognition is not supported in this browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setStatus('Processing...');
      setIsListening(false);
      return;
    }

    transcriptRef.current = '';
    setIsListening(true);
    recognitionRef.current.start();
  };

  return (
    <Shell>
      <div className="grid w-full gap-6">
        <Card title="Voice">
          <p className="max-w-2xl">
            Press start, speak your message, then press stop to send it to the assistant.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={toggleListening}
              disabled={isProcessing}
              className={[
                'rounded-full px-5 py-3 font-medium transition',
                isProcessing ? 'cursor-not-allowed opacity-70' : '',
                isListening
                  ? 'bg-rose-500 text-white hover:bg-rose-400'
                  : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300',
              ].join(' ')}
            >
              {isListening ? 'Stop Listening' : isProcessing ? 'Processing...' : 'Start Listening'}
            </button>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
              {status}
            </span>
          </div>

          {isProcessing ? <p className="mt-4 text-sm text-slate-300">Sending your message...</p> : null}

          {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
          {!supported ? (
            <p className="mt-4 text-sm text-amber-300">
              This browser does not support speech recognition.
            </p>
          ) : null}
        </Card>

        <div className="grid gap-4">
          {messages.length === 0 ? (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-slate-400">
              Your conversation will appear here.
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={[
                  'max-w-[85%] rounded-3xl px-4 py-3 text-sm leading-6 sm:max-w-[70%]',
                  message.role === 'user'
                    ? 'ml-0 rounded-bl-md bg-slate-100 text-slate-950'
                    : 'ml-auto rounded-br-md bg-cyan-400 text-slate-950',
                ].join(' ')}
              >
                <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide opacity-70">
                  {message.role === 'user' ? 'User' : 'AI'}
                </div>
                {message.text}
              </div>
            ))
          )}
        </div>
      </div>
    </Shell>
  );
}
