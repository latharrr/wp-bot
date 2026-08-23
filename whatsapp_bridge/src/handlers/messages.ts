import type { WAMessage, WASocket } from '@whiskeysockets/baileys';
import { internalClient } from '../http/internalClient.js';
import { phoneFromJid } from '../utils/phone.js';
import { handlePollCreation, handlePollUpdate } from './polls.js';

function extractText(msg: WAMessage): string | undefined {
  const m = msg.message;
  return m?.conversation ?? m?.extendedTextMessage?.text ?? m?.imageMessage?.caption ?? m?.videoMessage?.caption ?? undefined;
}

export async function handleIncomingMessage(sock: WASocket, msg: WAMessage): Promise<void> {
  const groupJid = msg.key.remoteJid;
  if (!groupJid || !groupJid.endsWith('@g.us') || msg.key.fromMe) return;

  if (msg.message?.pollCreationMessageV3 || msg.message?.pollCreationMessage) {
    await handlePollCreation(msg, groupJid);
    return;
  }
  if (msg.message?.pollUpdateMessage) {
    await handlePollUpdate(sock, msg, groupJid);
    return;
  }

  const text = extractText(msg);
  if (!text || !msg.key.id) return;

  const senderJid = msg.key.participant ?? msg.key.remoteJid ?? '';
  // In @lid-addressed groups, key.participant is an anonymized linked ID; key.participantAlt
  // carries the real phone-number JID when Baileys has resolved it (see groups.ts for the
  // same distinction on group member sync -- these must derive phone the same way, since
  // consent matching joins on member_phone across both).
  const senderPhoneJid = msg.key.participantAlt ?? senderJid;
  const replyTo = msg.message?.extendedTextMessage?.contextInfo?.stanzaId ?? undefined;

  await internalClient.message({
    group_jid: groupJid,
    sender_jid: senderJid,
    sender_phone: phoneFromJid(senderPhoneJid),
    sender_name: msg.pushName ?? null,
    message: text,
    message_id: msg.key.id,
    message_timestamp_ms: Number(msg.messageTimestamp ?? Date.now() / 1000) * 1000,
    reply_to_message_id: replyTo ?? null,
  });
}
