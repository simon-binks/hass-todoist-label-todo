# Todoist Label Todo

A Home Assistant custom integration that creates a native todo list entity for each Todoist label, enabling label-based task views alongside the standard project-based integration.

## Why?

The native Todoist integration syncs tasks by **project**. This integration syncs by **label**, which is useful for cross-project views like a GTD-style *Next Actions* list.

Key differences from the native integration:
- Filters by label instead of project
- Includes subtasks (the native integration excludes them)
- One todo entity per label

## Installation

### HACS (recommended)

1. In Home Assistant, go to **HACS → Custom Repositories**
2. Add `https://github.com/simon-binks/hass-todoist-label-todo` with category **Integration**
3. Install *Todoist Label Todo* via HACS
4. Restart Home Assistant

### Manual

Copy `custom_components/todoist_label_todo/` into your HA `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for *Todoist Label Todo*
3. Enter your Todoist API token (found under **Todoist Settings → Integrations → Developer**)
4. Select which labels to sync — each becomes a separate todo entity

To add or remove labels later, use the **Configure** option on the integration.

## How It Works

- Polls the Todoist API every minute (matching the native integration)
- Each task's `id` is used as the todo item `uid` directly — no workarounds
- Completing a task in HA calls `POST /tasks/{id}/close` in Todoist
- Reopening a task in HA calls `POST /tasks/{id}/reopen` in Todoist
