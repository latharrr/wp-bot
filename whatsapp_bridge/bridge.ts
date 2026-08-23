import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import { Boom } from '@hapi/boom';
import makeWASocket, {
  DisconnectReason,
  fetchLatestBaileysVersion,
  useMultiFileAuthState,
  type WASocket,
} from '@whiskeysockets/baileys';
import pino from 'pino';

import { config } from './src/config.js';
import { startControlServer } from './src/http/controlServer.js';
import { internalClient } from './src/http/internalClient.js';
import { syncAllGroups, syncOneGroup } from './src/handlers/groups.js';
import { handleIncomingMessage } from './src/handlers/messages.js';
import { handleReaction } from './src/handlers/reactions.js';

mkdirSync(config.logDir, { recursive: true });
mkdirSync(config.authDir, { recursive: true });

const logger = pino({ level: config.logLevel }, pino.destination(`${config.logDir}/bridge.log`));

let sock: WASocket | null = null;
let pairingCodeRequested = false;

function writePairingCode(code: string): void {
  mkdirSync(dirname(config.pairingCodeFile), { recursive: true });
  writeFileSync(config.pairingCodeFile, JSON.stringify({ code, generated_at: Date.now() }));
}

async function refreshGroups(): Promise<void> {
  if (sock) await syncAllGroups(sock);
}

async function start(): Promise<void> {
  const { state, saveCreds } = await useMultiFileAuthState(config.authDir);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: !config.usePairingCode,
  });

  sock.ev.on('creds.update', saveCreds);

  if (config.usePairingCode && config.phoneNumber && !sock.authState.creds.registered && !pairingCodeRequested) {
    // requestPairingCode sends a node over the raw websocket immediately; the connection
    // isn't open yet at this point (makeWASocket only starts connecting), so without this it
    // throws "Connection Closed" every time instead of ever producing a code.
    await sock.waitForSocketOpen();
    const code = await sock.requestPairingCode(config.phoneNumber);
    pairingCodeRequested = true;
    console.log(`Pairing code for ${config.phoneNumber}: ${code}`);
    writePairingCode(code);
  }

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect } = update;

    if (connection === 'connecting') {
      await internalClient.sessionEvent({ event: 'connecting' });
    }

    if (connection === 'open') {
      await internalClient.sessionEvent({ event: 'connected', phone_number: config.phoneNumber });
      console.log('WhatsApp bridge connected');
      await refreshGroups();
    }

    if (connection === 'close') {
      const statusCode = (lastDisconnect?.error as Boom | undefined)?.output?.statusCode;
      const loggedOut = statusCode === DisconnectReason.loggedOut;

      await internalClient.sessionEvent({
        event: loggedOut ? 'logged_out' : 'disconnected',
        status_code: statusCode,
      });

      if (loggedOut) {
        console.error('Session logged out; a fresh pairing is required.');
        return;
      }
      console.warn('Connection closed, reconnecting...', statusCode);
      await start();
    }
  });

  sock.ev.on('messages.upsert', async ({ messages }) => {
    for (const msg of messages) {
      try {
        await handleIncomingMessage(sock!, msg);
      } catch (err) {
        console.error('Failed to handle message:', err);
      }
    }
  });

  sock.ev.on('messages.reaction', async (reactions) => {
    for (const r of reactions) {
      try {
        await handleReaction(r.reaction, r.key.remoteJid);
      } catch (err) {
        console.error('Failed to handle reaction:', err);
      }
    }
  });

  sock.ev.on('group-participants.update', async (event) => {
    await syncOneGroup(sock!, event.id);
  });

  sock.ev.on('groups.update', async (updates) => {
    for (const g of updates) {
      if (g.id) await syncOneGroup(sock!, g.id);
    }
  });
}

startControlServer(() => sock, refreshGroups);

start().catch((err) => {
  console.error('Fatal error starting bridge:', err);
  process.exit(1);
});
