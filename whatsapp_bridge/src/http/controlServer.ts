import { timingSafeEqual } from 'node:crypto';
import express, { type Request, type Response } from 'express';
import type { WASocket } from '@whiskeysockets/baileys';
import { config } from '../config.js';

function isValidToken(provided: string | undefined): boolean {
  if (!provided) return false;
  const providedBuf = Buffer.from(provided);
  const expectedBuf = Buffer.from(config.controlToken);
  if (providedBuf.length !== expectedBuf.length) return false;
  return timingSafeEqual(providedBuf, expectedBuf);
}

/**
 * Small localhost-only server the Python side calls to reach into the live WhatsApp session --
 * force an immediate group resync, or properly unlink the device (not just stop our local
 * process). Separate shared-secret from the internal webhook direction (bridge -> Python) since
 * this is the opposite trust boundary.
 */
export function startControlServer(refreshGroups: (force?: boolean) => Promise<void>, getSocket: () => WASocket | null): void {
  const app = express();
  app.use(express.json());

  app.use((req: Request, res: Response, next) => {
    if (!isValidToken(req.header('x-control-token'))) {
      res.status(401).json({ error: 'invalid control token' });
      return;
    }
    next();
  });

  app.post('/refresh-groups', async (_req: Request, res: Response) => {
    await refreshGroups(true);
    res.json({ ok: true });
  });

  app.post('/logout', async (_req: Request, res: Response) => {
    const sock = getSocket();
    if (!sock) {
      res.status(503).json({ error: 'socket not connected' });
      return;
    }
    try {
      // sock.logout() tells WhatsApp's servers to actually unlink this device (it disappears
      // from Linked Devices on the phone too), as opposed to just stopping our local process --
      // which would leave a ghost linked device until WhatsApp times it out on its own.
      await sock.logout();
      res.json({ ok: true });
    } catch (err) {
      res.status(502).json({ error: err instanceof Error ? err.message : 'logout failed' });
    }
  });

  app.listen(config.controlPort, '127.0.0.1', () => {
    console.log(`Bridge control server listening on 127.0.0.1:${config.controlPort}`);
  });
}
