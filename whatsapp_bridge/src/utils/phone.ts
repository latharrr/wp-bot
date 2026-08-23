/** Normalizes a WhatsApp JID ("919876543210:12@s.whatsapp.net") down to a bare phone number. */
export function phoneFromJid(jid: string | undefined | null): string | undefined {
  if (!jid) return undefined;
  const bare = jid.split('@')[0]?.split(':')[0];
  if (!bare || !/^\d+$/.test(bare)) return undefined;
  return bare;
}

/**
 * Resolves a member/sender's real phone number, given their primary identity JID and (if
 * Baileys resolved it) a separate phone-number JID -- e.g. GroupParticipant.id + .phoneNumber,
 * or WAMessageKey.participant + .participantAlt.
 *
 * In @lid-addressed groups, WhatsApp frequently never discloses the real number for a
 * participant who isn't a known contact of the paired account (common in large community
 * groups) -- there is no real number to fall back to in that case. Never derive "phone" from
 * the bare digits of an @lid identifier itself; those are an anonymized ID, not a dialable
 * number, and presenting them as one is actively misleading to the operator.
 */
export function resolvePhone(primaryJid: string | undefined | null, phoneJid?: string | null): string | undefined {
  if (phoneJid) return phoneFromJid(phoneJid);
  if (primaryJid && !primaryJid.endsWith('@lid')) return phoneFromJid(primaryJid);
  return undefined;
}
