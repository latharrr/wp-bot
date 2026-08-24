import { timingSafeEqual } from 'node:crypto';
import express, { type Request, type Response } from 'express';
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
 * currently just "force an immediate group resync". Separate shared-secret from the internal
 * webhook direction (bridge -> Python) since this is the opposite trust boundary.
 */
export function startControlServer(refreshGroups: (force?: boolean) => Promise<void>): void {
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

  app.listen(config.controlPort, '127.0.0.1', () => {
    console.log(`Bridge control server listening on 127.0.0.1:${config.controlPort}`);
  });
}
