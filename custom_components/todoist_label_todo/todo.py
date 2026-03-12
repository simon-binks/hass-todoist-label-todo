"""Todo platform for Todoist Label Todo."""
from __future__ import annotations

import logging
from datetime import date, datetime

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TodoistLabelCoordinator

_LOGGER = logging.getLogger(__name__)


def _parse_due(due: dict | None) -> date | datetime | None:
    """Convert a Todoist due dict to a date or timezone-aware datetime."""
    if not due:
        return None
    if dt_str := due.get("datetime"):
        # e.g. "2024-01-15T09:00:00.000000Z" — normalise to +00:00 offset
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if d_str := due.get("date"):
        return date.fromisoformat(d_str)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one todo entity per configured label."""
    coordinators: dict[str, TodoistLabelCoordinator] = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TodoistLabelTodoEntity(coordinator) for coordinator in coordinators.values()
    )


class TodoistLabelTodoEntity(CoordinatorEntity[TodoistLabelCoordinator], TodoListEntity):
    """A todo list entity backed by a Todoist label."""

    _attr_supported_features = (
        TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )
    _attr_has_entity_name = True

    def __init__(self, coordinator: TodoistLabelCoordinator) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"todoist_label_{coordinator.label}"
        self._attr_name = coordinator.label

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return current todo items, mapped from Todoist tasks."""
        if not self.coordinator.data:
            return []
        return [
            TodoItem(
                uid=task["id"],
                summary=task["content"],
                status=(
                    TodoItemStatus.COMPLETED
                    if task.get("is_completed")
                    else TodoItemStatus.NEEDS_ACTION
                ),
                description=task.get("description") or None,
                due=_parse_due(task.get("due")),
            )
            for task in self.coordinator.data
        ]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Handle a status, description, or due-date change on a todo item."""
        # Status change
        if item.status == TodoItemStatus.COMPLETED:
            await self.coordinator.async_close_task(item.uid)
        elif item.status == TodoItemStatus.NEEDS_ACTION:
            await self.coordinator.async_reopen_task(item.uid)

        # Field updates (only send fields that were explicitly provided)
        updates: dict = {}
        if item.description is not None:
            updates["description"] = item.description
        if item.due is not None:
            if isinstance(item.due, datetime):
                updates["due_datetime"] = item.due.isoformat()
            else:
                updates["due_date"] = item.due.isoformat()

        if updates:
            await self.coordinator.async_update_task(item.uid, updates)

        await self.coordinator.async_request_refresh()
