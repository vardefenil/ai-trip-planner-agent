import type { SavedSession, ChatMessage } from '@/types/travel';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function sendChat(
  message: string,
  sessionId: string | null,
  history: Array<{ role: string; content: string }>
) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      conversation_history: history,
    }),
  });
  if (!res.ok) throw new Error(`Chat API error: ${res.status}`);
  return res.json();
}

export function streamTripPlan(
  query: string,
  sessionId: string | null,
  onEvent: (event: Record<string, unknown>) => void,
  onError: (err: string) => void,
  onDone: () => void
): () => void {
  const controller = new AbortController();

  fetch(`${API_BASE}/plan-trip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        onError(`API error: ${res.status}`);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        onError('No response stream');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onEvent(data);
              if (data.type === 'complete' || data.type === 'error') {
                onDone();
              }
            } catch {
              // ignore parse errors
            }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err.message);
        onDone();
      }
    });

  return () => controller.abort();
}

export async function fetchSessions(): Promise<SavedSession[]> {
  try {
    const res = await fetch(`${API_BASE}/sessions`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.sessions || [];
  } catch {
    return [];
  }
}

interface RawSessionMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type?: 'chat' | 'pipeline_start' | 'package_list' | 'booking' | 'error';
  timestamp?: string | number;
  payload?: {
    packages?: TripPackage[];
    booking_summary?: BookingSummary;
  };
}

export async function fetchSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  try {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.messages || []).map((m: RawSessionMessage) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      type: m.type,
      timestamp: new Date(m.timestamp || Date.now()),
      packages: m.payload?.packages,
      bookingSummary: m.payload?.booking_summary,
    }));
  } catch {
    return [];
  }
}

export async function deleteSessionApi(sessionId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
    return res.ok;
  } catch {
    return false;
  }
}
