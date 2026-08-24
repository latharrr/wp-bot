import type { WAMessage, WASocket } from '@whiskeysockets/baileys';
import { internalClient } from '../http/internalClient.js';
import { resolvePhone } from '../utils/phone.js';
import { waitForOnDemandHistory } from '../utils/historySync.js';

const PAGE_SIZE = 50;
// Pacing between successive on-demand history requests for the same group, so a deep backfill
// doesn't look like a burst of repeated history-sync traffic to WhatsApp's anti-abuse systems.
const PAGE_DELAY_MS = 4_000;
// A safety circuit breaker against an infinite loop bug, not an intended depth limit -- the
// operator asked to go "as far back as WhatsApp allows", which in practice always stops on its
// own well before this (WhatsApp's own on-demand history sync has a real, if undocumented, floor).
const MAX_PAGES = 500;

export type BackfillAnchor = { messageId: string; participant: string | null; timestampSec: number };
export type BackfillResult = { pagesFetched: number; messagesStored: number; stoppedReason: string };

function extractText(msg: WAMessage): string | undefined {
  const m = msg.message;
  return m?.conversation ?? m?.extendedTextMessage?.text ?? m?.imageMessage?.caption ?? m?.videoMessage?.caption ?? undefined;
}

async function forwardHistoricalMessage(msg: WAMessage, groupJid: string): Promise<boolean> {
  const text = extractText(msg);
  if (!text || !msg.key.id || msg.key.fromMe) return false;

  const senderJid = msg.key.participant ?? msg.key.remoteJid ?? '';
  const replyTo = msg.message?.extendedTextMessage?.contextInfo?.stanzaId ?? undefined;

  await internalClient.message({
    group_jid: groupJid,
    sender_jid: senderJid,
    sender_phone: resolvePhone(senderJid, msg.key.participantAlt),
    sender_name: msg.pushName ?? null,
    message: text,
    message_id: msg.key.id,
    message_timestamp_ms: Number(msg.messageTimestamp ?? Date.now() / 1000) * 1000,
    reply_to_message_id: replyTo ?? null,
  });
  return true;
}

/**
 * Manually-triggered deep backfill for one group: pages backward from `anchor` via WhatsApp's
 * on-demand history sync (the same mechanism polls.ts uses for one-off poll recovery), storing
 * every message it gets back, until WhatsApp stops returning anything further -- that's the real
 * boundary of what's available, not a guarantee of reaching the group's full history since
 * creation. Deliberately not run automatically or across groups at once (see the ban-risk notes
 * in the README) -- this is a one-group, operator-initiated action, called from the control
 * server's /backfill-history route.
 */
export async function backfillGroupHistory(sock: WASocket, groupJid: string, anchor: BackfillAnchor): Promise<BackfillResult> {
  let current = anchor;
  let pagesFetched = 0;
  let messagesStored = 0;

  while (pagesFetched < MAX_PAGES) {
    const anchorKey = {
      remoteJid: groupJid,
      id: current.messageId,
      fromMe: false,
      participant: current.participant ?? undefined,
    };

    let requestId: string;
    try {
      requestId = await sock.fetchMessageHistory(PAGE_SIZE, anchorKey, current.timestampSec);
    } catch (err) {
      console.error(`Backfill for ${groupJid} failed to request history at page ${pagesFetched}:`, err);
      return { pagesFetched, messagesStored, stoppedReason: 'request_failed' };
    }

    const messages = await waitForOnDemandHistory(sock, requestId, groupJid);
    if (!messages?.length) {
      console.log(`Backfill for ${groupJid} stopped: WhatsApp returned no further history after ${pagesFetched} page(s), ${messagesStored} message(s) stored`);
      return { pagesFetched, messagesStored, stoppedReason: 'exhausted' };
    }

    for (const msg of messages) {
      try {
        if (await forwardHistoricalMessage(msg, groupJid)) messagesStored += 1;
      } catch (err) {
        console.error(`Failed to store a historical message in ${groupJid}:`, err);
      }
    }
    pagesFetched += 1;

    const oldest = messages.reduce((min, m) => (Number(m.messageTimestamp ?? 0) < Number(min.messageTimestamp ?? 0) ? m : min));
    const oldestTimestampSec = Number(oldest.messageTimestamp ?? 0);
    if (!oldest.key.id || oldestTimestampSec <= 0 || oldestTimestampSec >= current.timestampSec) {
      // WhatsApp handed back the same or a newer boundary instead of moving further back --
      // stop rather than risk looping forever on an unexpected response shape.
      console.log(`Backfill for ${groupJid} stopped: no further progress after ${pagesFetched} page(s), ${messagesStored} message(s) stored`);
      return { pagesFetched, messagesStored, stoppedReason: 'no_progress' };
    }

    current = {
      messageId: oldest.key.id,
      participant: oldest.key.participant ?? null,
      timestampSec: oldestTimestampSec,
    };

    await new Promise((resolve) => setTimeout(resolve, PAGE_DELAY_MS));
  }

  console.warn(`Backfill for ${groupJid} hit the safety cap of ${MAX_PAGES} pages, ${messagesStored} message(s) stored`);
  return { pagesFetched, messagesStored, stoppedReason: 'max_pages' };
}
