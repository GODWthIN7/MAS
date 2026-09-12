import pytest
from uuid import uuid4

from app.models.agent import Agent, AgentRole, AgentStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.team import Team, TeamStatus
from app.services.agent_service import AgentService
from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.services.collaboration_service import CollaborationService
from app.services.orchestrator_service import OrchestratorService


class TestAgentService:
    """Tests for AgentService."""

    def setup_method(self):
        self.service = AgentService()

    def test_create_agent(self):
        agent = self.service.create_agent(
            name="Test Agent",
            role=AgentRole.DEVELOPER,
            expertise=["python"],
        )
        assert agent.name == "Test Agent"
        assert agent.role == AgentRole.DEVELOPER
        assert agent.status == AgentStatus.IDLE

    def test_list_agents(self):
        self.service.create_agent("Alice", AgentRole.ARCHITECT, [])
        self.service.create_agent("Bob", AgentRole.DEVELOPER, [])
        agents = self.service.list_agents()
        assert len(agents) == 2

    def test_find_agents_by_role(self):
        self.service.create_agent("Alice", AgentRole.ARCHITECT, [])
        self.service.create_agent("Bob", AgentRole.DEVELOPER, [])
        architects = self.service.find_agents_by_role(AgentRole.ARCHITECT)
        assert len(architects) == 1
        assert architects[0].name == "Alice"

    def test_agent_availability(self):
        agent = self.service.create_agent("Test", AgentRole.DEVELOPER, [], capacity=1)
        assert agent.is_available is True
        agent.active_tasks = 1
        assert agent.is_available is False

    def test_assign_task(self):
        agent = self.service.create_agent("Test", AgentRole.DEVELOPER, [], capacity=2)
        result = self.service.assign_task(agent.id)
        assert result is not None
        assert result.active_tasks == 1

    def test_complete_task(self):
        agent = self.service.create_agent("Test", AgentRole.DEVELOPER, [], capacity=2)
        self.service.assign_task(agent.id)
        result = self.service.complete_task(agent.id)
        assert result.active_tasks == 0
        assert result.total_completed == 1


class TestTaskService:
    """Tests for TaskService."""

    def setup_method(self):
        self.service = TaskService()

    def test_create_task(self):
        task = self.service.create_task(
            title="Test Task",
            description="Test description",
            priority=TaskPriority.HIGH,
        )
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH

    def test_list_pending_tasks(self):
        self.service.create_task("Task 1")
        self.service.create_task("Task 2")
        pending = self.service.list_pending_tasks()
        assert len(pending) == 2

    def test_task_dependency(self):
        task1 = self.service.create_task("Task 1")
        task2 = self.service.create_task("Task 2")
        self.service.add_dependency(task2.id, task1.id)
        task2 = self.service.get_task(task2.id)
        assert task1.id in task2.dependencies

    def test_ready_tasks(self):
        task1 = self.service.create_task("Task 1")
        task2 = self.service.create_task("Task 2")
        self.service.add_dependency(task2.id, task1.id)
        ready = self.service.list_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == task1.id

    def test_task_workflow(self):
        task = self.service.create_task("Test Task")
        agent_id = uuid4()

        self.service.assign_task(task.id, agent_id)
        task = self.service.get_task(task.id)
        assert task.status == TaskStatus.ASSIGNED

        self.service.start_task(task.id)
        task = self.service.get_task(task.id)
        assert task.status == TaskStatus.IN_PROGRESS

        self.service.complete_task(task.id, result="Done", actual_hours=2.0)
        task = self.service.get_task(task.id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Done"


class TestTeamService:
    """Tests for TeamService."""

    def setup_method(self):
        self.service = TeamService()

    def test_create_team(self):
        team = self.service.create_team(
            name="Test Team",
            description="Test description",
        )
        assert team.name == "Test Team"
        assert team.status == TeamStatus.ACTIVE

    def test_add_agent_to_team(self):
        team = self.service.create_team("Test Team")
        agent_id = uuid4()
        result = self.service.add_agent_to_team(team.id, agent_id)
        assert result is not None
        assert agent_id in result.agent_ids

    def test_team_stats(self):
        team = self.service.create_team("Test Team")
        agent_id = uuid4()
        self.service.add_agent_to_team(team.id, agent_id)
        task_id = uuid4()
        self.service.add_active_task(team.id, task_id)

        stats = self.service.get_team_stats(team.id)
        assert stats["total_agents"] == 1
        assert stats["active_tasks"] == 1


class TestOrchestratorService:
    """Tests for OrchestratorService."""

    def setup_method(self):
        self.agent_service = AgentService()
        self.task_service = TaskService()
        self.team_service = TeamService()
        self.collab_service = CollaborationService()
        self.orchestrator = OrchestratorService(
            self.agent_service,
            self.task_service,
            self.team_service,
            self.collab_service,
        )

    def test_assign_task_to_agent(self):
        agent = self.agent_service.create_agent("Alice", AgentRole.DEVELOPER, [])
        task = self.task_service.create_task("Test Task")

        success = self.orchestrator.assign_task_to_agent(task.id, agent.id)
        assert success is True

        agent = self.agent_service.get_agent(agent.id)
        assert agent.active_tasks == 1

    def test_complete_task_workflow(self):
        agent = self.agent_service.create_agent("Alice", AgentRole.DEVELOPER, [])
        team = self.team_service.create_team("Test Team")
        task = self.task_service.create_task("Test Task", team_id=team.id)

        self.orchestrator.assign_task_to_agent(task.id, agent.id)
        self.orchestrator.start_task(task.id)
        self.team_service.add_active_task(team.id, task.id)

        success = self.orchestrator.complete_task_workflow(
            task.id, result="Done", actual_hours=2.0
        )
        assert success is True

        task = self.task_service.get_task(task.id)
        assert task.status == TaskStatus.COMPLETED

    def test_workflow_status(self):
        agent = self.agent_service.create_agent("Alice", AgentRole.DEVELOPER, [])
        team = self.team_service.create_team("Test Team")
        self.team_service.add_agent_to_team(team.id, agent.id)

        status = self.orchestrator.get_workflow_status(team.id)
        assert status["team_id"] == team.id
        assert status["agents"]["total"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
