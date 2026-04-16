import { useEffect, useRef, useState } from 'react';
import { Shell, Card } from '../components/Layout';
import { apiUrl } from '../lib/api';

const VAPI_PUBLIC_KEY = import.meta.env.VITE_VAPI_PUBLIC_KEY;
const VAPI_ASSISTANT_ID = import.meta.env.VITE_VAPI_ASSISTANT_ID;
let vapiClientPromise = null;

async function getVapiClient() {
  if (!VAPI_PUBLIC_KEY) {
    throw new Error('Vapi public key is missing.');
  }

  if (!vapiClientPromise) {
    vapiClientPromise = import(
      /* @vite-ignore */ 'https://esm.sh/@vapi-ai/web'
    ).then(({ default: Vapi }) => new Vapi(VAPI_PUBLIC_KEY));
  }

  return vapiClientPromise;
}

export default function Voice() {
  const vapiRef = useRef(null);
  const conversationRef = useRef([]);
  const [isListening, setIsListening] = useState(false);
  const [status, setStatus] = useState('Idle');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const appendMessage = (role, text) => {
    const cleanText = String(text || '').trim();
    if (!cleanText) return;

    setMessages((current) => {
      const last = current[current.length - 1];
      if (last && last.role === role && last.text === cleanText) {
        return current;
      }
      conversationRef.current.push(`${role}: ${cleanText}`);
      return [...current, { role, text: cleanText }];
    });
  };

  const syncConversation = (entries) => {
    const nextMessages = (entries || [])
      .map((entry) => {
        const role = entry?.role === 'assistant' ? 'ai' : 'user';
        const text = String(entry?.message || entry?.content || entry?.transcript || '').trim();

        if (!text) {
          return null;
        }

        return { role, text };
      })
      .filter(Boolean);

    if (nextMessages.length === 0) {
      return;
    }

    const conversationLines = nextMessages.map((item) => `${item.role}: ${item.text}`);
    conversationRef.current = conversationLines;
    setMessages(nextMessages);
  };

  useEffect(() => {
    let mounted = true;

    const initVapi = async () => {
      try {
        if (!VAPI_PUBLIC_KEY || !VAPI_ASSISTANT_ID) {
          if (mounted) {
            setError('Vapi keys are missing from .env.');
          }
          return;
        }

        const vapi = await getVapiClient();
        const handleCallStart = () => {
          if (!mounted) return;
          setIsListening(true);
          setStatus('Listening...');
          setError('');
        };

        const handleMessage = (rawMsg) => {
          if (!mounted) return;

          const msg = rawMsg?.message ?? rawMsg;

          if (msg.type === 'transcript' && msg.transcriptType === 'final') {
            const role = msg.role === 'assistant' ? 'ai' : 'user';
            appendMessage(role, msg.transcript);
          } else if (msg.type === 'conversation-update') {
            const conversation = msg.messages || msg.conversation || msg.messagesOpenAIFormatted || [];
            syncConversation(conversation);
          } else if (msg.type === 'speech-update' && msg.role === 'assistant' && msg.status === 'started') {
            setStatus('Listening...');
          }
        };

        const handleError = () => {
          if (!mounted) return;
          setIsListening(false);
          setStatus('Idle');
          setError('Unable to connect to the voice assistant.');
        };

        const handleCallEnd = async () => {
          if (!mounted) return;
          setIsListening(false);
          setStatus('Saving...');
          setSaving(true);

          try {
            const conversationText = conversationRef.current.join('\n');
            if (conversationText) {
              await fetch(apiUrl('/memory'), {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  user_id: 'demo_user',
                  issue_type: 'conversation',
                  text: conversationText,
                }),
              });
            }
          } catch {
            // Keep the UI quiet for demo usability.
          } finally {
            if (mounted) {
              setSaving(false);
              setStatus('Idle');
            }
          }
        };

        vapi.on('call-start', handleCallStart);
        vapi.on('message', handleMessage);
        vapi.on('error', handleError);
        vapi.on('call-end', handleCallEnd);

        vapiRef.current = vapi;
        vapiRef.current.__voiceHandlers = {
          handleCallStart,
          handleMessage,
          handleError,
          handleCallEnd,
        };
      } catch {
        if (mounted) {
          setError('Voice SDK could not load.');
        }
      }
    };

    initVapi();

    return () => {
      mounted = false;
      if (vapiRef.current) {
        const handlers = vapiRef.current.__voiceHandlers;
        if (handlers && typeof vapiRef.current.off === 'function') {
          vapiRef.current.off('call-start', handlers.handleCallStart);
          vapiRef.current.off('message', handlers.handleMessage);
          vapiRef.current.off('error', handlers.handleError);
          vapiRef.current.off('call-end', handlers.handleCallEnd);
        }
        delete vapiRef.current.__voiceHandlers;
        vapiRef.current = null;
      }
    };
  }, []);

  const startListening = async () => {
    setError('');

    if (!vapiRef.current) {
      setError('Voice assistant is not ready yet.');
      return;
    }

    if (isListening) return;

    try {
      setStatus('Connecting...');
      conversationRef.current = [];
      setMessages([]);
      await vapiRef.current.start(VAPI_ASSISTANT_ID);
    } catch {
      setStatus('Idle');
      setError('Unable to start the voice assistant.');
    }
  };

  const stopListening = () => {
    if (!vapiRef.current || !isListening) {
      return;
    }

    vapiRef.current.stop();
    setIsListening(false);
    setStatus('Saving...');
  };

  return (
    <Shell>
      <div className="grid w-full gap-6">
        <Card title="Voice">
          <p className="max-w-2xl">
            Press start to open the assistant. It should speak first, then listen for your reply.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={startListening}
              disabled={isListening}
              className={[
                'rounded-full px-5 py-3 font-medium transition',
                isListening
                  ? 'cursor-not-allowed bg-cyan-400 text-slate-950 opacity-60'
                  : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300',
              ].join(' ')}
            >
              Start Listening
            </button>
            <button
              onClick={stopListening}
              disabled={!isListening}
              className={[
                'rounded-full px-5 py-3 font-medium transition',
                isListening
                  ? 'bg-rose-500 text-white hover:bg-rose-400'
                  : 'cursor-not-allowed bg-rose-500 text-white opacity-60',
              ].join(' ')}
            >
              Stop Listening
            </button>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
              {status}
            </span>
          </div>

          {saving ? <p className="mt-4 text-sm text-slate-300">Saving conversation to history...</p> : null}

          {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
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
