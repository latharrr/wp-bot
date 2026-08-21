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

/** Poll-creation messages, keyed by message id, kept in memory so incoming vote-update
 * messages (which only carry an encrypted delta) can be decrypted against the original poll.
 * Baileys' getAggregateVotesInPollMessage needs the creation message's encryption key. */
const pollCreationCache = new Map<string, WAMessage>();

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

  const creationMsg = pollCreationCache.get(pollCreationMessageId);
  if (!creationMsg || !update.vote) {
    console.warn(`No cached poll creation for ${pollCreationMessageId}; skipping vote (bridge likely restarted mid-poll)`);
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
