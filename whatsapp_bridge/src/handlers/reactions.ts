import type { proto } from '@whiskeysockets/baileys';
import { internalClient } from '../http/internalClient.js';
import { phoneFromJid } from '../utils/phone.js';

export async function handleReaction(reactionMsg: proto.IReaction, remoteJid: string | null | undefined): Promise<void> {
  if (!remoteJid || !remoteJid.endsWith('@g.us')) return;

  const targetMessageId = reactionMsg.key?.id;
  const reactorJid = reactionMsg.key?.participant ?? remoteJid;
  const emoji = reactionMsg.text;
  if (!targetMessageId || !emoji) return; // empty text = reaction removed, not an opt-in signal

  await internalClient.reaction({
    group_jid: remoteJid,
    reactor_jid: reactorJid,
    reactor_phone: phoneFromJid(reactorJid),
    target_message_id: targetMessageId,
    emoji,
    timestamp_ms: Date.now(),
  });
}
