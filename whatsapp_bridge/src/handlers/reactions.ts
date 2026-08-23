import type { proto } from '@whiskeysockets/baileys';
import { internalClient } from '../http/internalClient.js';
import { resolvePhone } from '../utils/phone.js';

export async function handleReaction(
  reactionMsg: proto.IReaction,
  remoteJid: string | null | undefined,
  reactorJid: string | null | undefined,
  reactorJidAlt: string | null | undefined,
): Promise<void> {
  if (!remoteJid || !remoteJid.endsWith('@g.us')) return;

  // reactionMsg.key references the message being reacted TO (its .participant is that
  // message's original author, e.g. our own bot for a consent-prompt) -- NOT who reacted.
  // The reactor's identity is the outer envelope's key.participant, passed in separately.
  const targetMessageId = reactionMsg.key?.id;
  const emoji = reactionMsg.text;
  if (!targetMessageId || !emoji || !reactorJid) return; // empty text = reaction removed, not an opt-in signal

  await internalClient.reaction({
    group_jid: remoteJid,
    reactor_jid: reactorJid,
    reactor_phone: resolvePhone(reactorJid, reactorJidAlt),
    target_message_id: targetMessageId,
    emoji,
    timestamp_ms: Date.now(),
  });
}
