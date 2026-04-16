import { useEffect, useState } from 'react';
import { Shell, Card } from '../components/Layout';

const LOCAL_HISTORY_KEY = 'voiceaid-history';
const MOCK_HISTORY_ITEMS = [
  {
    id: 'mock-1',
    issue_summary:
      "I told my landlord the ceiling had been leaking for weeks, and now part of it has fallen in. I need help understanding what I can say to push for repairs without making things worse.",
    date_time: '2026-04-16T09:15:00+05:30',
  },
  {
    id: 'mock-2',
    issue_summary:
      "My employer has delayed my salary again and keeps saying it will be cleared next week. I want to know what options I have if this keeps happening.",
    date_time: '2026-04-15T18:40:00+05:30',
  },
  {
    id: 'mock-3',
    issue_summary:
      "A bike hit my parked car and the rider left before I could get their details. I have a photo from a neighbor, but I am not sure what the right next step is.",
    date_time: '2026-04-14T11:05:00+05:30',
  },
  {
    id: 'mock-4',
    issue_summary:
      "I paid an advance to a coaching center, but they changed the schedule and refused to refund anything. I just want to know how to ask for my money back properly.",
    date_time: '2026-04-13T16:25:00+05:30',
  },
];

const normalizeHistoryItems = (rawItems) =>
  rawItems
    .map((item, index) => {
      const summary =
        item.issue_summary || item.summary || item.issue || item.text || 'Untitled issue';
      const dateValue = item.date_time || item.datetime || item.created_at || item.timestamp || '';
      const time = dateValue ? new Date(dateValue).getTime() : 0;

      return {
        id: item.id || `${index}`,
        summary,
        dateLabel: dateValue ? new Date(dateValue).toLocaleString() : 'Unknown date',
        time,
      };
    })
    .sort((a, b) => b.time - a.time);

const getLocalHistory = () => {
  if (typeof window === 'undefined') {
    return normalizeHistoryItems(MOCK_HISTORY_ITEMS);
  }

  const existing = window.localStorage.getItem(LOCAL_HISTORY_KEY);
  if (!existing) {
    window.localStorage.setItem(LOCAL_HISTORY_KEY, JSON.stringify(MOCK_HISTORY_ITEMS));
    return normalizeHistoryItems(MOCK_HISTORY_ITEMS);
  }

  try {
    const parsed = JSON.parse(existing);
    if (Array.isArray(parsed) && parsed.length > 0) {
      return normalizeHistoryItems(parsed);
    }
  } catch {
    // Ignore malformed local history and restore the mock dataset.
  }

  window.localStorage.setItem(LOCAL_HISTORY_KEY, JSON.stringify(MOCK_HISTORY_ITEMS));
  return normalizeHistoryItems(MOCK_HISTORY_ITEMS);
};

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadHistory = () => {
      setLoading(true);
      setError('');
      setItems(getLocalHistory());
      setLoading(false);
    };

    loadHistory();
  }, []);

  return (
    <Shell>
      <div className="grid w-full gap-6">
        <Card title="Case History">
          <p className="max-w-2xl">
            A simple view of stored issues from memory, with the latest cases shown first.
          </p>
        </Card>

        {loading ? <div className="text-sm text-slate-300">Loading history...</div> : null}
        {error ? <div className="text-sm text-rose-300">{error}</div> : null}

        {!loading && !error && items.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-slate-400">
            No case history found.
          </div>
        ) : null}

        <div className="grid gap-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-lg shadow-slate-950/20"
            >
              <div className="text-base font-medium text-white">{item.summary}</div>
              <div className="mt-2 text-sm text-slate-300">{item.dateLabel}</div>
            </div>
          ))}
        </div>
      </div>
    </Shell>
  );
}
