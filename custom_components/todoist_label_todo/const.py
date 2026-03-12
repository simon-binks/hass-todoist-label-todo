"""Constants for Todoist Label Todo."""
from datetime import timedelta

DOMAIN = "todoist_label_todo"
SCAN_INTERVAL = timedelta(minutes=1)
TODOIST_API_BASE = "https://api.todoist.com/api/v1"
CONF_API_TOKEN = "api_token"
CONF_LABELS = "labels"
