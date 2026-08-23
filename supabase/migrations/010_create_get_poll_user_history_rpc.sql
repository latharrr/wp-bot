-- Ported from the reference repo. Given a list of phone numbers, return the historical
-- purchase/vote features the scoring heuristic needs. This is a stub: adapt the FROM clauses to
-- your actual purchase-history tables before relying on it in production.
create or replace function get_poll_user_history(mobiles text[])
returns table (
    mobile text,
    total_purchases integer,
    last_purchase_date date,
    purchases_last_30_days integer,
    purchases_last_60_days integer,
    total_yes_votes integer,
    last_vote_converted boolean,
    n_2_vote_converted boolean
)
language sql
stable
as $$
    select
        m.mobile,
        coalesce(history.total_purchases, 0),
        history.last_purchase_date,
        coalesce(history.purchases_last_30_days, 0),
        coalesce(history.purchases_last_60_days, 0),
        coalesce(history.total_yes_votes, 0),
        history.last_vote_converted,
        history.n_2_vote_converted
    from unnest(mobiles) as m(mobile)
    left join lateral (
        select
            pp.mobile,
            count(*) as total_purchases,
            max(pp.poll_date) as last_purchase_date,
            count(*) filter (where pp.poll_date >= current_date - interval '30 days') as purchases_last_30_days,
            count(*) filter (where pp.poll_date >= current_date - interval '60 days') as purchases_last_60_days,
            count(*) filter (where pp.vote = 'yes') as total_yes_votes,
            bool_or(pp.vote = 'yes') filter (where pp.poll_date = (
                select max(poll_date) from poll_prediction where mobile = m.mobile
            )) as last_vote_converted,
            null::boolean as n_2_vote_converted
        from poll_prediction pp
        where pp.mobile = m.mobile
        group by pp.mobile
    ) history on true;
$$;
