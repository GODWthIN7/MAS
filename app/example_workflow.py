from uuid import UUID

from app.models.agent import AgentRole, AgentStatus
from app.models.task import TaskPriority, TaskStatus
from app.core.services import (
    get_agent_service,
    get_task_service,
    get_team_service,
    get_orchestrator_service,
)


def demo_workflow():
    """Demonstrate a complete multi-agent workflow."""
    # Initialize services
    agent_service = get_agent_service()
    task_service = get_task_service()
    team_service = get_team_service()
    orchestrator = get_orchestrator_service()

    print("\n=== MAS Multi-Agent Development Team Demo ===\n")

    # 1. Create agents with different roles
    print("1. Creating agents...")
    architect = agent_service.create_agent(
        name="Alice",
        role=AgentRole.ARCHITECT,
        expertise=["system-design", "api-design"],
        capacity=3,
    )
    developer = agent_service.create_agent(
        name="Bob",
        role=AgentRole.DEVELOPER,
        expertise=["python", "fastapi", "testing"],
        capacity=5,
    )
    tester = agent_service.create_agent(
        name="Charlie",
        role=AgentRole.TESTER,
        expertise=["testing", "qa", "performance"],
        capacity=4,
    )
    coordinator = agent_service.create_agent(
        name="Diana",
        role=AgentRole.COORDINATOR,
        expertise=["coordination", "communication"],
        capacity=2,
    )
    print(f"  ✓ Created 4 agents: {architect.name}, {developer.name}, {tester.name}, {coordinator.name}")

    # 2. Create a team
    print("\n2. Creating development team...")
    team = team_service.create_team(
        name="Backend Team",
        description="Core API development team",
        team_lead_id=coordinator.id,
    )
    team_service.add_agent_to_team(team.id, architect.id)
    team_service.add_agent_to_team(team.id, developer.id)
    team_service.add_agent_to_team(team.id, tester.id)
    team_service.add_agent_to_team(team.id, coordinator.id)
    print(f"  ✓ Team '{team.name}' created with {team.total_agents} agents")

    # 3. Create tasks
    print("\n3. Creating tasks...")
    design_task = task_service.create_task(
        title="Design API Architecture",
        description="Create REST API design for agent management",
        priority=TaskPriority.HIGH,
        required_expertise=["system-design"],
        team_id=team.id,
        estimated_hours=4,
    )
    implementation_task = task_service.create_task(
        title="Implement Agent Service",
        description="Develop AgentService with CRUD operations",
        priority=TaskPriority.HIGH,
        required_expertise=["python", "fastapi"],
        team_id=team.id,
        estimated_hours=8,
    )
    # Make implementation dependent on design
    task_service.add_dependency(implementation_task.id, design_task.id)

    testing_task = task_service.create_task(
        title="Test Agent Service",
        description="Write comprehensive tests for AgentService",
        priority=TaskPriority.MEDIUM,
        required_expertise=["testing"],
        team_id=team.id,
        estimated_hours=6,
    )
    # Make testing dependent on implementation
    task_service.add_dependency(testing_task.id, implementation_task.id)

    print(f"  ✓ Created 3 tasks with dependencies:")
    print(f"    - {design_task.title}")
    print(f"    - {implementation_task.title} (depends on design)")
    print(f"    - {testing_task.title} (depends on implementation)")

    # 4. Assign and execute first task (no dependencies)
    print("\n4. Starting workflow execution...")
    print(f"  - Assigning '{design_task.title}' to {architect.name}...")
    orchestrator.assign_task_to_agent(design_task.id, architect.id)
    orchestrator.start_task(design_task.id)
    print(f"    ✓ Task started")

    print(f"  - Working on task... (simulated)")
    orchestrator.complete_task_workflow(
        design_task.id,
        result="API architecture designed with FastAPI framework",
        actual_hours=3.5,
    )
    print(f"    ✓ Task completed in 3.5 hours")

    # 5. Now implementation task is ready (dependency resolved)
    print(f"\n5. Second task is now ready for assignment...")
    ready_tasks = task_service.list_ready_tasks()
    print(f"  - Ready tasks: {[t.title for t in ready_tasks]}")

    print(f"  - Assigning '{implementation_task.title}' to {developer.name}...")
    orchestrator.assign_task_to_agent(implementation_task.id, developer.id)
    orchestrator.start_task(implementation_task.id)
    print(f"    ✓ Task started")

    print(f"  - Working on task... (simulated)")
    orchestrator.complete_task_workflow(
        implementation_task.id,
        result="AgentService implemented with full CRUD operations",
        actual_hours=8.2,
    )
    print(f"    ✓ Task completed in 8.2 hours")

    # 6. Testing task ready
    print(f"\n6. Testing task ready for execution...")
    ready_tasks = task_service.list_ready_tasks()
    print(f"  - Ready tasks: {[t.title for t in ready_tasks]}")

    print(f"  - Assigning '{testing_task.title}' to {tester.name}...")
    orchestrator.assign_task_to_agent(testing_task.id, tester.id)
    orchestrator.start_task(testing_task.id)
    print(f"    ✓ Task started")

    print(f"  - Working on task... (simulated)")
    orchestrator.complete_task_workflow(
        testing_task.id,
        result="All tests passed. 95% code coverage achieved.",
        actual_hours=5.8,
    )
    print(f"    ✓ Task completed in 5.8 hours")

    # 7. Report final status
    print("\n7. Workflow completion report...")
    workflow_status = orchestrator.get_workflow_status(team.id)
    print(f"\n  Team: {workflow_status['team_name']}")
    print(f"  Status: {workflow_status['team_status']}")
    print(f"  Agents: {workflow_status['agents']['total']} total")
    print(f"    - Available: {workflow_status['agents']['available']}")
    print(f"    - Busy: {workflow_status['agents']['busy']}")
    print(f"  Tasks: {workflow_status['tasks']['completed']} completed, {workflow_status['tasks']['active']} active")
    print(f"  Team Efficiency: {workflow_status['team_efficiency']}%")

    print("\n  Agent Statistics:")
    for agent_id in team.agent_ids:
        stats = agent_service.get_agent_stats(agent_id)
        print(f"    - {stats['name']} ({stats['role']}): {stats['total_completed']} completed, {stats['active_tasks']} active")

    print("\n=== Demo Complete ===\n")


if __name__ == "__main__":
    demo_workflow()
