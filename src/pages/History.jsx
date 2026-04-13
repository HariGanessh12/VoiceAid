import { useEffect, useState } from 'react';
import { Shell, Card } from '../components/Layout';
import { apiUrl } from '../lib/api';

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        setError('');

        const response = await fetch(apiUrl('/history?user_id=demo_user'));
        if (!response.ok) {
          throw new Error('Request failed');
        }

        const data = await response.json();
        const rawItems = Array.isArray(data)
          ? data
          : data?.history || data?.items || data?.results || [];

        const normalized = rawItems
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

        setItems(normalized);
      } catch {
        setError('Unable to load history right now.');
      } finally {
        setLoading(false);
      }
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
