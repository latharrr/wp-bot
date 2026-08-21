'use client';

import { use, useEffect, useState } from 'react';
import { api } from '@/lib/apiClient';
import { PollVoterTable } from '@/components/PollVoterTable';

export default function PollDetailPage({ params }: { params: Promise<{ groupJid: string; pollId: string }> }) {
  const { groupJid: encodedGroupJid, pollId: encodedPollId } = use(params);
  const groupJid = decodeURIComponent(encodedGroupJid);
  const pollMessageId = decodeURIComponent(encodedPollId);

  const [poll, setPoll] = useState<any>(null);

  useEffect(() => {
    api.get<any>(`/api/v1/groups/${encodeURIComponent(groupJid)}/polls/${encodeURIComponent(pollMessageId)}`).then(setPoll);
  }, [groupJid, pollMessageId]);

  if (!poll) return <p className="muted">Loading...</p>;

  return (
    <div>
      <h2>Poll detail</h2>
      <PollVoterTable groupJid={groupJid} pollMessageId={pollMessageId} poll={poll} />
    </div>
  );
}
