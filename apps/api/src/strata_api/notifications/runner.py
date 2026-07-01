"""Orchestrate watch-event email digests for every user with watches.

For each distinct user:
  1. derive events since the user's last_notified_at (capped to a 7-day lookback)
  2. resolve their email
  3. render + send a digest
  4. stamp last_notified_at on all of the user's watches — success only

Failures are isolated per user so one bad send never blocks the rest. The
summary counts are returned for the admin endpoint to surface.
"""
from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from strata_api.db.models.watch import Watch
from strata_api.notifications.digest import render_digest
from strata_api.notifications.emailer import EmailSender
from strata_api.notifications.user_emails import EmailResolver
from strata_api.watch_events import derive_events

logger = logging.getLogger(__name__)

_DEFAULT_LOOKBACK_DAYS = 7


@dataclass(frozen=True)
class NotificationSummary:
    """Outcome counts for a single notification run."""

    users: int
    sent: int
    skipped_no_events: int
    skipped_no_email: int
    failed: int


def _user_cutoff(
    watches: list[Watch], now: datetime.datetime, lookback_days: int
) -> datetime.datetime:
    """The earliest timestamp an event may have to count as fresh for this user.

    NULL last_notified_at (a never-notified or brand-new watch) means look back
    the full window; otherwise resume from the last digest — but never earlier
    than the lookback cap.
    """
    baseline = now - datetime.timedelta(days=lookback_days)
    stamps = [w.last_notified_at for w in watches]
    if any(stamp is None for stamp in stamps):
        return baseline
    return max(min(stamps), baseline)


def run_notifications(
    engine,
    *,
    sender: EmailSender,
    resolve_email: EmailResolver,
    now: datetime.datetime | None = None,
    lookback_days: int = _DEFAULT_LOOKBACK_DAYS,
) -> NotificationSummary:
    """Send digests to all users with fresh watch events. See module docstring."""
    now = now or datetime.datetime.utcnow()

    with Session(engine) as s:
        user_ids = list(s.execute(select(Watch.user_id).distinct()).scalars().all())

        sent = skipped_no_events = skipped_no_email = failed = 0
        for user_id in user_ids:
            try:
                watches = list(
                    s.execute(select(Watch).where(Watch.user_id == user_id)).scalars().all()
                )
                watched_egids = {w.egid for w in watches}
                cutoff = _user_cutoff(watches, now, lookback_days)

                events = derive_events(s, watched_egids, cutoff)
                if not events:
                    skipped_no_events += 1
                    continue

                email = resolve_email(user_id)
                if not email:
                    skipped_no_email += 1
                    continue

                digest = render_digest(events)
                if digest is None:  # defensive — events is non-empty here
                    skipped_no_events += 1
                    continue

                sender.send(email, digest.subject, digest.body)

                for watch in watches:
                    watch.last_notified_at = now
                s.commit()
                sent += 1
            except Exception:
                s.rollback()
                logger.exception("Notification failed for user %s", user_id)
                failed += 1

    return NotificationSummary(
        users=len(user_ids),
        sent=sent,
        skipped_no_events=skipped_no_events,
        skipped_no_email=skipped_no_email,
        failed=failed,
    )
