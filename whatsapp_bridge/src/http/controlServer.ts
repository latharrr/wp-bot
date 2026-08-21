import express, { type Request, type Response } from 'express';
import type { WASocket } from '@whiskeysockets/baileys';
import { config } from '../config.js';

/**
 * Small localhost-only server the Python side calls to reach into the live WhatsApp session --
 * currently just "post this consent-prompt message into a group". Separate shared-secret from
 * the internal webhook direction (bridge -> Python) since this is the opposite trust boundary.
 */
export function startControlServer(getSocket: () => WASocket | null, refreshGroups: () => Promise<void>): void {
  const app = express();
  app.use(express.json());

  app.use((req: Request, res: Response, next) => {
    if (req.header('x-control-token') !== config.controlToken) {
      res.status(401).json({ error: 'invalid control token' });
      return;
    }
    next();
  });

  app.post('/send-message', async (req: Request, res: Response) => {
    const sock = getSocket();
    if (!sock) {
      res.status(503).json({ error: 'socket not connected' });
      return;
    }
    const { group_jid: groupJid, text } = req.body ?? {};
    if (!groupJid || !text) {
      res.status(400).json({ error: 'group_jid and text are required' });
      return;
    }
    const sent = await sock.sendMessage(groupJid, { text });
    res.json({ message_id: sent?.key?.id ?? null });
  });

  app.post('/refresh-groups', async (_req: Request, res: Response) => {
    await refreshGroups();
    res.json({ ok: true });
  });

  app.listen(config.controlPort, '127.0.0.1', () => {
    console.log(`Bridge control server listening on 127.0.0.1:${config.controlPort}`);
  });
}
