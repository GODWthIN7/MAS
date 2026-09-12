from uuid import UUID

from app.models.agent import Agent, AgentRole, AgentStatus


class AgentService:
    """Service for managing agents."""

    def __init__(self):
        self.agents: dict[UUID, Agent] = {}

    def create_agent(
        self, name: str, role: AgentRole, expertise: list[str], capacity: int = 5
    ) -> Agent:
        """Create a new agent."""
        agent = Agent(
            name=name,
            role=role,
            expertise=expertise,
            capacity=capacity,
        )
        self.agents[agent.id] = agent
        return agent

    def get_agent(self, agent_id: UUID) -> Agent | None:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> list[Agent]:
        """List all agents."""
        return list(self.agents.values())

    def list_available_agents(self) -> list[Agent]:
        """List agents available to take new tasks."""
        return [a for a in self.agents.values() if a.is_available]

    def find_agents_by_expertise(self, expertise: list[str]) -> list[Agent]:
        """Find agents with required expertise."""
        return [a for a in self.agents.values() if a.can_handle(expertise)]

    def find_agents_by_role(self, role: AgentRole) -> list[Agent]:
        """Find agents with specific role."""
        return [a for a in self.agents.values() if a.role == role]

    def set_agent_status(self, agent_id: UUID, status: AgentStatus) -> Agent | None:
        """Update agent status."""
        agent = self.get_agent(agent_id)
        if agent:
            agent.status = status
            return agent
        return None

    def assign_task(self, agent_id: UUID) -> Agent | None:
        """Increment active task count for agent."""
        agent = self.get_agent(agent_id)
        if agent and agent.active_tasks < agent.capacity:
            agent.active_tasks += 1
            agent.status = AgentStatus.BUSY if agent.active_tasks > 0 else AgentStatus.IDLE
            return agent
        return None

    def complete_task(self, agent_id: UUID) -> Agent | None:
        """Decrement active task count and increment completed count."""
        agent = self.get_agent(agent_id)
        if agent:
            agent.active_tasks = max(0, agent.active_tasks - 1)
            agent.total_completed += 1
            agent.status = AgentStatus.IDLE if agent.active_tasks == 0 else AgentStatus.BUSY
            return agent
        return None

    def get_agent_stats(self, agent_id: UUID) -> dict | None:
        """Get agent performance statistics."""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        return {
            "agent_id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "status": agent.status,
            "capacity": agent.capacity,
            "active_tasks": agent.active_tasks,
            "total_completed": agent.total_completed,
            "utilization": round((agent.active_tasks / agent.capacity) * 100, 2),
        }
