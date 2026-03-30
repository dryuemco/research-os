"""decomposition and coding handoff foundation

Revision ID: 0004_decomposition_and_handoff_foundation
Revises: 0003_proposal_factory_foundation
Create Date: 2026-03-30 03:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_decomposition_and_handoff_foundation"
down_revision = "0003_proposal_factory_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "execution_plans",
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("plan_name", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("policy_json", sa.JSON(), nullable=False),
        sa.Column("ambiguity_log", sa.JSON(), nullable=False),
        sa.Column("unresolved_dependency_log", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_execution_plans_proposal_id"), "execution_plans", ["proposal_id"], unique=False
    )
    op.create_index(op.f("ix_execution_plans_state"), "execution_plans", ["state"], unique=False)

    op.create_table(
        "execution_objectives",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("objective_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("success_metrics", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_execution_objectives_execution_plan_id"),
        "execution_objectives",
        ["execution_plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_execution_objectives_objective_code"),
        "execution_objectives",
        ["objective_code"],
        unique=False,
    )

    op.create_table(
        "work_packages",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("wp_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("objective_ref", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_work_packages_execution_plan_id"),
        "work_packages",
        ["execution_plan_id"],
        unique=False,
    )
    op.create_index(op.f("ix_work_packages_wp_code"), "work_packages", ["wp_code"], unique=False)

    op.create_table(
        "deliverables",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("work_package_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_package_id"], ["work_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deliverables_code"), "deliverables", ["code"], unique=False)
    op.create_index(
        op.f("ix_deliverables_execution_plan_id"),
        "deliverables",
        ["execution_plan_id"],
        unique=False,
    )

    op.create_table(
        "milestones",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("due_hint", sa.String(length=64), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_milestones_code"), "milestones", ["code"], unique=False)
    op.create_index(
        op.f("ix_milestones_execution_plan_id"), "milestones", ["execution_plan_id"], unique=False
    )

    op.create_table(
        "risk_items",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("risk_code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("mitigation", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_risk_items_execution_plan_id"), "risk_items", ["execution_plan_id"], unique=False
    )
    op.create_index(op.f("ix_risk_items_risk_code"), "risk_items", ["risk_code"], unique=False)

    op.create_table(
        "validation_activities",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("task_code", sa.String(length=64), nullable=False),
        sa.Column("validation_type", sa.String(length=64), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_validation_activities_execution_plan_id"),
        "validation_activities",
        ["execution_plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_validation_activities_task_code"),
        "validation_activities",
        ["task_code"],
        unique=False,
    )

    op.add_column("task_graphs", sa.Column("execution_plan_id", sa.String(), nullable=True))
    op.create_foreign_key(
        None, "task_graphs", "execution_plans", ["execution_plan_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index(
        op.f("ix_task_graphs_execution_plan_id"), "task_graphs", ["execution_plan_id"], unique=False
    )

    op.create_table(
        "engineering_tickets",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("task_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("dependencies", sa.JSON(), nullable=False),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False),
        sa.Column("definition_of_done", sa.JSON(), nullable=False),
        sa.Column("suggested_provider_policy", sa.JSON(), nullable=False),
        sa.Column("suggested_task_type", sa.String(length=64), nullable=False),
        sa.Column("repository_target", sa.JSON(), nullable=False),
        sa.Column("branch_suggestion", sa.String(length=128), nullable=False),
        sa.Column("context_pack_refs", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_engineering_tickets_execution_plan_id"),
        "engineering_tickets",
        ["execution_plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_engineering_tickets_task_code"), "engineering_tickets", ["task_code"], unique=False
    )

    op.create_table(
        "coding_work_units",
        sa.Column("execution_plan_id", sa.String(), nullable=False),
        sa.Column("engineering_ticket_id", sa.String(), nullable=False),
        sa.Column("repository_target", sa.JSON(), nullable=False),
        sa.Column("branch_name", sa.String(length=128), nullable=False),
        sa.Column("patch_scope", sa.JSON(), nullable=False),
        sa.Column("suggested_test_artifacts", sa.JSON(), nullable=False),
        sa.Column("rollback_risk_label", sa.String(length=32), nullable=False),
        sa.Column("human_approval_required", sa.Boolean(), nullable=False),
        sa.Column("routing_intent", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["engineering_ticket_id"], ["engineering_tickets.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_coding_work_units_engineering_ticket_id"),
        "coding_work_units",
        ["engineering_ticket_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_coding_work_units_execution_plan_id"),
        "coding_work_units",
        ["execution_plan_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_coding_work_units_execution_plan_id"), table_name="coding_work_units")
    op.drop_index(
        op.f("ix_coding_work_units_engineering_ticket_id"), table_name="coding_work_units"
    )
    op.drop_table("coding_work_units")

    op.drop_index(op.f("ix_engineering_tickets_task_code"), table_name="engineering_tickets")
    op.drop_index(
        op.f("ix_engineering_tickets_execution_plan_id"), table_name="engineering_tickets"
    )
    op.drop_table("engineering_tickets")

    op.drop_index(op.f("ix_task_graphs_execution_plan_id"), table_name="task_graphs")
    op.drop_constraint(None, "task_graphs", type_="foreignkey")
    op.drop_column("task_graphs", "execution_plan_id")

    op.drop_index(op.f("ix_validation_activities_task_code"), table_name="validation_activities")
    op.drop_index(
        op.f("ix_validation_activities_execution_plan_id"), table_name="validation_activities"
    )
    op.drop_table("validation_activities")

    op.drop_index(op.f("ix_risk_items_risk_code"), table_name="risk_items")
    op.drop_index(op.f("ix_risk_items_execution_plan_id"), table_name="risk_items")
    op.drop_table("risk_items")

    op.drop_index(op.f("ix_milestones_execution_plan_id"), table_name="milestones")
    op.drop_index(op.f("ix_milestones_code"), table_name="milestones")
    op.drop_table("milestones")

    op.drop_index(op.f("ix_deliverables_execution_plan_id"), table_name="deliverables")
    op.drop_index(op.f("ix_deliverables_code"), table_name="deliverables")
    op.drop_table("deliverables")

    op.drop_index(op.f("ix_work_packages_wp_code"), table_name="work_packages")
    op.drop_index(op.f("ix_work_packages_execution_plan_id"), table_name="work_packages")
    op.drop_table("work_packages")

    op.drop_index(op.f("ix_execution_objectives_objective_code"), table_name="execution_objectives")
    op.drop_index(
        op.f("ix_execution_objectives_execution_plan_id"), table_name="execution_objectives"
    )
    op.drop_table("execution_objectives")

    op.drop_index(op.f("ix_execution_plans_state"), table_name="execution_plans")
    op.drop_index(op.f("ix_execution_plans_proposal_id"), table_name="execution_plans")
    op.drop_table("execution_plans")
