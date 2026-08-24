import { proto, type WAMessage, type WASocket } from '@whiskeysockets/baileys';

const HISTORY_RECOVERY_TIMEOUT_MS = 15_000;

/**
 * Waits for the on-demand history sync response matching `requestId`, scoped to one group.
 * Shared between the poll-creation recovery path (polls.ts) and the manual full-history
 * backfill path (backfill.ts) -- both page backward through WhatsApp's on-demand history sync
 * the same way, just for different reasons and at different scale.
 */
export function waitForOnDemandHistory(sock: WASocket, requestId: string, groupJid: string): Promise<WAMessage[] | undefined> {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (result: WAMessage[] | undefined) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      sock.ev.off('messaging-history.set', handler);
      resolve(result);
    };

    const timeout = setTimeout(() => finish(undefined), HISTORY_RECOVERY_TIMEOUT_MS);

    const handler = (payload: {
      messages: WAMessage[];
      syncType?: proto.HistorySync.HistorySyncType | null;
      peerDataRequestSessionId?: string | null;
    }) => {
      if (payload.syncType !== proto.HistorySync.HistorySyncType.ON_DEMAND || payload.peerDataRequestSessionId !== requestId) {
        return;
      }
      finish(payload.messages.filter((message) => message.key.remoteJid === groupJid));
    };

    sock.ev.on('messaging-history.set', handler);
  });
}
