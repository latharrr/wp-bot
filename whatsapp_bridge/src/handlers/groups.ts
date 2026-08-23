import type { WASocket } from '@whiskeysockets/baileys';
import { internalClient } from '../http/internalClient.js';
import { phoneFromJid } from '../utils/phone.js';

/** Full resync of every group the paired account participates in -- no single-group scoping,
 * this bridge tracks the whole account (unlike the reference repo's single-target-group bridge). */
export async function syncAllGroups(sock: WASocket): Promise<void> {
  const groupsById = await sock.groupFetchAllParticipating();
  const groups = Object.values(groupsById).map((meta) => ({
    group_jid: meta.id,
    subject: meta.subject,
    participants: meta.participants.map((p) => ({
      jid: p.id,
      // In groups using @lid (privacy) addressing, p.id is an anonymized linked ID, not a
      // real dialable number -- Baileys separately resolves the real number to phoneNumber
      // (an @s.whatsapp.net JID) when it's known. Fall back to p.id for ordinary groups where
      // it's already the phone-number JID and phoneNumber is unset.
      phone: phoneFromJid(p.phoneNumber ?? p.id),
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
            phone: phoneFromJid(p.phoneNumber ?? p.id),
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
