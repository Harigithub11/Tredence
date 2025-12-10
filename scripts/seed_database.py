"""Seed Database with Example Workflows

Creates the code_review workflow graph in the database.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from sqlalchemy import select
from app.database.connection import get_session_context
from app.database.models import GraphModel


async def seed_code_review_workflow():
    """Create the code_review workflow graph in the database."""

    # Define the workflow graph structure
    graph_definition = {
        "nodes": {
            "extract": {
                "type": "lambda",
                "function": "extract_functions_node"
            },
            "complexity": {
                "type": "lambda",
                "function": "calculate_complexity_node"
            },
            "detect": {
                "type": "lambda",
                "function": "detect_issues_node"
            },
            "suggest": {
                "type": "lambda",
                "function": "suggest_improvements_node"
            },
            "check": {
                "type": "lambda",
                "function": "check_quality_node"
            }
        },
        "edges": [
            {"from": "extract", "to": "complexity"},
            {"from": "complexity", "to": "detect"},
            {"from": "detect", "to": "suggest"},
            {"from": "suggest", "to": "check"},
            {"from": "check", "to": "suggest", "condition": "should_loop"}
        ],
        "entry_point": "extract"
    }

    async with get_session_context() as session:
        # Check if the workflow already exists
        result = await session.execute(
            select(GraphModel).where(GraphModel.name == "code_review")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("[OK] code_review workflow already exists in database")
            print(f"  ID: {existing.id}")
            print(f"  Created: {existing.created_at}")
            return existing

        # Create new workflow
        workflow = GraphModel(
            name="code_review",
            description="Hybrid code review workflow with complexity analysis, issue detection, and AI-powered suggestions",
            definition=graph_definition,
            version=1,
            is_active=True
        )

        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)

        print("[OK] Created code_review workflow in database")
        print(f"  ID: {workflow.id}")
        print(f"  Name: {workflow.name}")
        print(f"  Version: {workflow.version}")

        return workflow


async def main():
    print("=" * 70)
    print("DATABASE SEEDING - Example Workflows")
    print("=" * 70)
    print()

    try:
        # Seed code_review workflow
        workflow = await seed_code_review_workflow()

        print()
        print("=" * 70)
        print("Database seeding completed successfully!")
        print("=" * 70)
        print()
        print("Available workflows:")
        print(f"  - {workflow.name}: {workflow.description}")
        print()
        print("You can now run workflows via the API:")
        print("  POST /graph/run")
        print(f'  {{"graph_name": "{workflow.name}", "initial_state": {{"code": "...", "quality_threshold": 70}}, "use_llm": false}}')
        print()

    except Exception as e:
        print(f"[ERROR] Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
