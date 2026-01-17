import caldav


class TaskService:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self.client = caldav.DAVClient(url=url, username=username, password=password)

    def get_tasks(self):
        principal = self.client.principal()
        calendars = principal.calendars()

        all_tasks = []

        for calendar in calendars:
            todos = calendar.todos()
            for todo in todos:
                task = self._parse_vtodo(todo.data)
                all_tasks.append(task)

        return all_tasks

    def _parse_vtodo(self, vtodo_string):
        todo = {}
        for line in vtodo_string.split("\n"):
            line = line.strip()
            if line.startswith("SUMMARY:"):
                summary = line.split(":", 1)[1]
                todo["summary"] = summary
            if line.startswith("STATUS:"):
                status = line.split(":", 1)[1]
                todo["status"] = status
            if line.startswith("UID:"):
                uid = line.split(":", 1)[1]
                todo["uid"] = uid

        return todo

    def get_incomplete_tasks(self):
        return [task for task in self.get_tasks() if task["status"] != "COMPLETED"]
