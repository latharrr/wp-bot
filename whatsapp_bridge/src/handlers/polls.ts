import {
  decryptPollVote,
  getAggregateVotesInPollMessage,
  getKeyAuthor,
  jidNormalizedUser,
  type WAMessage,
  type WASocket,
} from '@whiskeysockets/baileys';
import { internalClient } from '../http/internalClient.js';
import { phoneFromJid } from '../utils/phone.js';
import { waitForOnDemandHistory } from '../utils/historySync.js';

/** Poll-creation messages, keyed by message id, kept in memory so incoming vote-update
 * messages (which only carry an encrypted delta) can be decrypted against the original poll.
 * Baileys' getAggregateVotesInPollMessage needs the creation message's encryption key. */
const pollCreationCache = new Map<string, WAMessage>();

const HISTORY_RECOVERY_PAGE_SIZE = 20;

/**
 * Ported (in scoped-down form) from poison-br09/whatsapp-propensity-scoring: that repo
 * continuously tracks the oldest message ever seen per group and proactively backfills on every
 * reconnect. That's meaningfully more surface area to get wrong against a live paired session,
 * and more repeated history-sync traffic for WhatsApp's anti-abuse systems to look at (see the
 * ban-risk notes in the README). This version only asks for history reactively, anchored at the
 * vote message itself, exactly when a vote references a poll-creation message we don't have
 * cached -- at most one request per occurrence, not a standing background job. (For a deliberate,
 * manually-triggered deep backfill of ordinary messages, see backfill.ts instead.)
 */

async function recoverMissingPollCreation(
  sock: WASocket,
  anchorMessage: WAMessage,
  pollCreationMessageId: string,
): Promise<WAMessage | undefined> {
  const groupJid = anchorMessage.key.remoteJid;
  if (!groupJid || !anchorMessage.key.id) return undefined;

  try {
    const requestId = await sock.fetchMessageHistory(
      HISTORY_RECOVERY_PAGE_SIZE,
      anchorMessage.key,
      Number(anchorMessage.messageTimestamp ?? Math.floor(Date.now() / 1000)),
    );
    console.log(`Requested on-demand history to recover poll creation ${pollCreationMessageId} in ${groupJid}`);

    const messages = await waitForOnDemandHistory(sock, requestId, groupJid);
    if (!messages?.length) {
      console.warn(`On-demand history recovery for poll ${pollCreationMessageId} returned nothing`);
      return undefined;
    }

    for (const message of messages) {
      const pollCreation = message.message?.pollCreationMessageV3 ?? message.message?.pollCreationMessage;
      if (pollCreation && message.key.id) {
        pollCreationCache.set(message.key.id, message);
      }
    }
    return pollCreationCache.get(pollCreationMessageId);
  } catch (err) {
    console.error(`Failed to recover poll creation ${pollCreationMessageId} via history backfill:`, err);
    return undefined;
  }
}

export async function handlePollCreation(msg: WAMessage, groupJid: string): Promise<void> {
  const pollCreation = msg.message?.pollCreationMessageV3 ?? msg.message?.pollCreationMessage;
  const messageId = msg.key.id;
  if (!pollCreation || !messageId) return;

  pollCreationCache.set(messageId, msg);

  const options = (pollCreation.options ?? []).map((o) => o.optionName ?? '').filter(Boolean);
  await internalClient.pollCreated({
    group_jid: groupJid,
    poll_message_id: messageId,
    poll_title: pollCreation.name ?? '',
    poll_options: options,
    poll_created_at_ms: Number(msg.messageTimestamp ?? Date.now() / 1000) * 1000,
  });
  console.log(`Poll created in ${groupJid}: "${pollCreation.name}"`);
}

export async function handlePollUpdate(sock: WASocket, msg: WAMessage, groupJid: string): Promise<void> {
  const update = msg.message?.pollUpdateMessage;
  const pollCreationMessageId = update?.pollCreationMessageKey?.id;
  if (!update || !pollCreationMessageId) return;

  let creationMsg = pollCreationCache.get(pollCreationMessageId);
  if (!creationMsg) {
    console.warn(`No cached poll creation for ${pollCreationMessageId}; attempting on-demand history recovery`);
    creationMsg = await recoverMissingPollCreation(sock, msg, pollCreationMessageId);
  }
  if (!creationMsg || !update.vote) {
    console.warn(`Could not recover poll creation for ${pollCreationMessageId}; skipping vote`);
    return;
  }

  const meId = jidNormalizedUser(sock.user?.id ?? '');
  const pollCreatorJid = getKeyAuthor(update.pollCreationMessageKey, meId);
  const voterJid = getKeyAuthor(msg.key, meId);
  const pollEncKey = creationMsg.message?.messageContextInfo?.messageSecret;
  if (!pollEncKey) {
    console.warn(`Poll ${pollCreationMessageId} has no messageSecret; cannot decrypt votes`);
    return;
  }

  const decryptedVote = decryptPollVote(update.vote, {
    pollCreatorJid,
    pollMsgId: pollCreationMessageId,
    pollEncKey,
    voterJid,
  });

  const aggregated = getAggregateVotesInPollMessage({
    message: creationMsg.message!,
    pollUpdates: [
      {
        pollUpdateMessageKey: msg.key,
        vote: decryptedVote,
        senderTimestampMs: Number(msg.messageTimestamp ?? Date.now() / 1000) * 1000,
      },
    ],
  });

  const selectedOptions = aggregated.filter((a) => a.voters.includes(voterJid)).map((a) => a.name);
  const pollTitle = creationMsg.message?.pollCreationMessageV3?.name ?? creationMsg.message?.pollCreationMessage?.name ?? '';
  const pollOptions = (
    creationMsg.message?.pollCreationMessageV3?.options ?? creationMsg.message?.pollCreationMessage?.options ?? []
  )
    .map((o) => o.optionName ?? '')
    .filter(Boolean);
  const voteTimestampMs = Number(msg.messageTimestamp ?? Date.now() / 1000) * 1000;

  await internalClient.pollVote({
    dedupe_key: `${pollCreationMessageId}:${voterJid}:${voteTimestampMs}`,
    group_jid: groupJid,
    poll_message_id: pollCreationMessageId,
    poll_title: pollTitle,
    poll_options: pollOptions,
    voter_jid: voterJid,
    voter_phone: phoneFromJid(voterJid),
    voter_name: msg.pushName ?? null,
    selected_options: selectedOptions,
    vote_timestamp_ms: voteTimestampMs,
  });
  console.log(`Poll vote in ${groupJid} from ${phoneFromJid(voterJid)}: ${selectedOptions.join(', ')}`);
}
