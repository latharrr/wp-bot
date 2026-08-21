-- The structural consent gate. Every "who is this person" read for contacts or keyword hits --
-- both the dashboard detail views AND the .xlsx export endpoints -- must select from these views
-- and NEVER read group_members / keyword_match directly. That makes the double-consent rule
-- (group consented AND member opted in) impossible to accidentally bypass with a sloppy query,
-- because the join conditions live in the database, not scattered across application code.
create or replace view exportable_contacts as
select
    gm.group_jid,
    g.group_name,
    gm.member_jid,
    gm.phone,
    gm.display_name,
    mc.opted_in_at
from group_members gm
join groups g
    on g.group_jid = gm.group_jid
    and g.consent_status = 'consented'
join member_consent mc
    on mc.group_jid = gm.group_jid
    and mc.member_phone = gm.phone
    and mc.opted_in = true
    and mc.opted_out_at is null;

create or replace view exportable_keyword_matches as
select
    km.id,
    km.keyword,
    km.group_jid,
    g.group_name,
    km.sender_jid,
    km.sender_name,
    km.sender_phone,
    km.message,
    km.message_id,
    km.message_date
from keyword_match km
join groups g
    on g.group_jid = km.group_jid
    and g.consent_status = 'consented'
join member_consent mc
    on mc.group_jid = km.group_jid
    and mc.member_phone = km.sender_phone
    and mc.opted_in = true
    and mc.opted_out_at is null;
