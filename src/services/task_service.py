from typing import Any

import caldav


class TaskService:
    STATUS_COMPLETED = "COMPLETED"
    STATUS_NEEDS_ACTION = "NEEDS-ACTION"

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self.client = caldav.DAVClient(url=url, username=username, password=password)

    def get_tasks(self) -> list[dict[str, str]]:
        """Fetch all tasks from CalDAV calendars.
        Returns:
            List of task dicts with keys: summary, status, uid
        """
        principal = self.client.principal()
        calendars = principal.calendars()

        return [
            self._parse_vtodo(todo.data)
            for calendar in calendars
            for todo in calendar.todos()
        ]

    def _parse_vtodo(self, vtodo_string: str) -> dict[str, str]:
        todo = {}
        for line in vtodo_string.split("\n"):
            line = line.strip()
            if line.startswith("SUMMARY:"):
                todo["summary"] = line.split(":", 1)[1].strip()
            elif line.startswith("STATUS:"):
                todo["status"] = line.split(":", 1)[1].strip()
            elif line.startswith("UID:"):
                todo["uid"] = line.split(":", 1)[1].strip()

        return todo

    def get_incomplete_tasks(self) -> list[dict[str, str]]:
        """Fetches a list of tasks without the status of COMPLETED."""
        return [
            task
            for task in self.get_tasks()
            if task.get("status") != self.STATUS_COMPLETED
        ]
