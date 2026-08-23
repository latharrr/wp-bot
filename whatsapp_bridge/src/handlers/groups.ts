import type { WASocket } from '@whiskeysockets/baileys';
import { internalClient } from '../http/internalClient.js';
import { resolvePhone } from '../utils/phone.js';

/** Full resync of every group the paired account participates in -- no single-group scoping,
 * this bridge tracks the whole account (unlike the reference repo's single-target-group bridge). */
export async function syncAllGroups(sock: WASocket): Promise<void> {
  const groupsById = await sock.groupFetchAllParticipating();
  const groups = Object.values(groupsById).map((meta) => ({
    group_jid: meta.id,
    subject: meta.subject,
    participants: meta.participants.map((p) => ({
      jid: p.id,
      // WhatsApp frequently never discloses a real number for @lid participants who aren't a
      // contact of the paired account (common in large community groups) -- resolvePhone
      // returns undefined rather than fabricating one from the anonymized @lid digits.
      phone: resolvePhone(p.id, p.phoneNumber),
      display_name: p.notify ?? null,
      is_admin: p.admin === 'admin' || p.admin === 'superadmin',
    })),
  }));

  if (groups.length === 0) return;
  await internalClient.groupsSync({ groups });
  console.log(`Synced ${groups.length} group(s)`);
}

/** Incremental resync of a single group after a participants/metadata update event. */
export async function syncOneGroup(sock: WASocket, groupJid: string): Promise<void> {
  try {
    const meta = await sock.groupMetadata(groupJid);
    await internalClient.groupsSync({
      groups: [
        {
          group_jid: meta.id,
          subject: meta.subject,
          participants: meta.participants.map((p) => ({
            jid: p.id,
            phone: resolvePhone(p.id, p.phoneNumber),
            display_name: p.notify ?? null,
            is_admin: p.admin === 'admin' || p.admin === 'superadmin',
          })),
        },
      ],
    });
  } catch (err) {
    console.error(`Failed to resync group ${groupJid}:`, err);
  }
}
