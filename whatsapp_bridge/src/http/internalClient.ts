import { config } from '../config.js';

async function post(path: string, body: unknown): Promise<void> {
  const response = await fetch(`${config.internalBaseUrl}${path}`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-internal-token': config.internalToken,
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    console.error(`internal POST ${path} failed: ${response.status} ${text}`);
  }
}

export const internalClient = {
  sessionEvent: (body: { event: string; phone_number?: string; status_code?: number; occurred_at_ms?: number }) =>
    post('/internal/whatsapp/session-event', body),

  groupsSync: (body: { groups: unknown[] }) => post('/internal/whatsapp/groups-sync', body),

  pollCreated: (body: unknown) => post('/internal/whatsapp/poll-created', body),

  pollVote: (body: unknown) => post('/internal/whatsapp/poll-vote', body),

  message: (body: unknown) => post('/internal/whatsapp/message', body),

  reaction: (body: unknown) => post('/internal/whatsapp/reaction', body),
};
