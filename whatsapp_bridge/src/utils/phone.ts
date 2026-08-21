/** Normalizes a WhatsApp JID ("919876543210:12@s.whatsapp.net") down to a bare phone number. */
export function phoneFromJid(jid: string | undefined | null): string | undefined {
  if (!jid) return undefined;
  const bare = jid.split('@')[0]?.split(':')[0];
  if (!bare || !/^\d+$/.test(bare)) return undefined;
  return bare;
}
