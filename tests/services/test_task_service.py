import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.services.task_service import TaskService


class TestTaskService:

    @pytest.fixture
    def mock_caldav_client(self):
        """Mock CalDAV client"""
        with patch("src.services.task_service.caldav.DAVClient") as mock:
            yield mock

    @pytest.fixture
    def mock_vtodo_data(self):
        """Sample VTODO data from CalDAV"""
        return [
            {
                "summary": "Buy milk",
                "status": "NEEDS-ACTION",
                "uid": "123",
            },
            {
                "summary": "Buy bread",
                "status": "NEEDS-ACTION",
                "uid": "456",
            },
            {
                "summary": "Buy eggs",
                "status": "COMPLETED",
                "uid": "789",
            },
        ]

    def test_task_service_initializes_with_credentials(self, mock_caldav_client):
        """TaskService should initialize with CalDAV credentials"""
        service = TaskService(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="app-specific-password",
        )

        assert service.url == "https://caldav.icloud.com/"
        assert service.username == "test@icloud.com"
        assert service.password == "app-specific-password"

        # Should create CalDAV client
        mock_caldav_client.assert_called_once_with(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="app-specific-password",
        )

    def test_task_service_get_tasks_returns_all_tasks(
        self, mock_caldav_client, mock_vtodo_data
    ):
        """get_tasks() should return all VTODO items"""
        # Setup mock to return tasks
        mock_principal = Mock()
        mock_calendar = Mock()
        mock_todos = []

        for todo_data in mock_vtodo_data:
            mock_todo = Mock()
            mock_todo.data = f"""BEGIN:VCALENDAR
BEGIN:VTODO
SUMMARY:{todo_data['summary']}
STATUS:{todo_data['status']}
UID:{todo_data['uid']}
END:VTODO
END:VCALENDAR"""
            mock_todos.append(mock_todo)

        mock_calendar.todos.return_value = mock_todos
        mock_principal.calendars.return_value = [mock_calendar]
        mock_caldav_client.return_value.principal.return_value = mock_principal

        service = TaskService(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="test-password",
        )

        tasks = service.get_tasks()

        assert len(tasks) == 3
        assert tasks[0]["summary"] == "Buy milk"
        assert tasks[2]["summary"] == "Buy eggs"

    def test_task_service_get_incomplete_tasks_filters_completed(
        self, mock_caldav_client, mock_vtodo_data
    ):
        """get_incomplete_tasks() should return only incomplete tasks"""
        # Setup mock (same as above)
        mock_principal = Mock()
        mock_calendar = Mock()
        mock_todos = []

        for todo_data in mock_vtodo_data:
            mock_todo = Mock()
            mock_todo.data = f"""BEGIN:VCALENDAR
                            BEGIN:VTODO
                            SUMMARY:{todo_data['summary']}
                            STATUS:{todo_data['status']}
                            UID:{todo_data['uid']}
                            END:VTODO
                            END:VCALENDAR"""
            mock_todos.append(mock_todo)

        mock_calendar.todos.return_value = mock_todos
        mock_principal.calendars.return_value = [mock_calendar]
        mock_caldav_client.return_value.principal.return_value = mock_principal

        service = TaskService(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="test-password",
        )

        incomplete_tasks = service.get_incomplete_tasks()

        # Should only return 2 tasks (milk, bread - not eggs)
        assert len(incomplete_tasks) == 2
        assert all(task["status"] != "COMPLETED" for task in incomplete_tasks)
        assert "Buy eggs" not in [task["summary"] for task in incomplete_tasks]
