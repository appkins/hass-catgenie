"""Calendar platform for CatGenie litter box activity.

Surfaces the cat-visit and cleaning-cycle history from the pet-statistics
endpoint as a calendar. Each poll fetches only the records since the previous
fetch and merges them into an accumulating, deduplicated store, so the calendar
builds up history over time without re-pulling the whole window each time.

Modeled on the Home Assistant Rain Bird calendar platform.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util

from .data import FlushResponse, PetStatistics, VisitResponse
from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry, CatGenieCoordinator

PARALLEL_UPDATES = 0

# On first refresh, seed this much history.
_INITIAL_LOOKBACK = timedelta(days=30)
# Re-fetch a small overlap before the last fetch so boundary records aren't
# missed; duplicates are collapsed by uid.
_FETCH_OVERLAP = timedelta(minutes=5)
# Cleaning cycles only report an end time, so render them as a short marker.
_CLEANING_MARKER = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    coordinator = entry.runtime_data
    async_add_entities([CatGenieActivityCalendar(coordinator=coordinator)])


def _visit_to_event(visit: VisitResponse) -> CalendarEvent | None:
    """Convert a visit record into a CalendarEvent, or None if unusable."""
    if not visit.timestamp:
        return None
    start = dt_util.utc_from_timestamp(visit.timestamp / 1000)
    duration = visit.fields.duration_seconds or 0
    # Ensure a non-zero span so the event renders.
    end = start + timedelta(seconds=max(duration, 1))
    return CalendarEvent(
        start=start,
        end=end,
        summary="Litter box visit",
        description=f"Duration: {duration}s",
        uid=f"visit-{visit.timestamp}",
    )


def _flush_to_event(flush: FlushResponse) -> CalendarEvent | None:
    """Convert a cleaning-cycle record into a CalendarEvent, or None."""
    if not flush.timestamp:
        return None
    # Only the cycle end time is reported, so anchor the marker to it.
    end = dt_util.utc_from_timestamp(flush.timestamp / 1000)
    start = end - _CLEANING_MARKER
    status = "aborted" if flush.fields.aborted else "completed"
    return CalendarEvent(
        start=start,
        end=end,
        summary="Cleaning cycle",
        description=f"Cleaning cycle {status}",
        uid=f"flush-{flush.timestamp}",
    )


def _build_events(stats: PetStatistics) -> list[CalendarEvent]:
    """Build calendar events (visits + cleaning cycles) from statistics."""
    candidates = [_visit_to_event(visit) for visit in stats.visit_responses]
    candidates += [_flush_to_event(flush) for flush in stats.flush_responses]
    return [event for event in candidates if event is not None]


class CatGenieActivityCalendar(CatGenieEntity, CalendarEntity):
    """A calendar of cat litter box visits and cleaning cycles."""

    _attr_translation_key = "activity"
    _unique_id_suffix = "activity"

    def __init__(self, coordinator: CatGenieCoordinator) -> None:
        """Initialize the calendar entity."""
        super().__init__(coordinator)
        # Accumulated events keyed by uid (dedupes across overlapping fetches).
        self._events: dict[str, CalendarEvent] = {}
        self._last_fetch: datetime | None = None

    @property
    def event(self) -> CalendarEvent | None:
        """Return the active event if one is in progress, else the latest."""
        now = dt_util.utcnow()
        events = self._events.values()
        active = [e for e in events if e.start <= now <= e.end]
        if active:
            return max(active, key=lambda e: e.start)
        past = [e for e in events if e.start <= now]
        return max(past, key=lambda e: e.start) if past else None

    async def async_update(self) -> None:
        """Fetch only records since the last fetch and merge them in."""
        now = dt_util.utcnow()
        if self._last_fetch is None:
            start = now - _INITIAL_LOOKBACK
        else:
            start = self._last_fetch - _FETCH_OVERLAP
        await self._async_fetch_and_merge(start)
        self._last_fetch = now

    async def async_get_events(
        self,
        hass: HomeAssistant,  # noqa: ARG002
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events within the requested range from the merged store."""
        # Ensure the requested window is covered (e.g. scrolling back in time).
        await self._async_fetch_and_merge(start_date)
        return sorted(
            (
                event
                for event in self._events.values()
                if event.end > start_date and event.start < end_date
            ),
            key=lambda event: event.start,
        )

    async def _async_fetch_and_merge(self, start_time: datetime) -> None:
        """Fetch statistics from ``start_time`` and merge into the store."""
        raw = await self.coordinator.client.async_get_pet_statistics(
            start_time=start_time,
        )
        stats = PetStatistics.from_dict(raw)
        for event in _build_events(stats):
            if event.uid is not None:
                self._events[event.uid] = event
