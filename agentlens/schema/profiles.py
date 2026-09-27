"""Agent and tool profiles for AgentLens.

Defines the capabilities, tool semantics, and action keywords for different
agent domains (e.g. customer_support, coding_agent).
"""
from typing import Optional
from pydantic import BaseModel, Field


class ToolCapability(BaseModel):
    name: str
    purpose: str
    action_keywords: list[str] = Field(default_factory=list)
    is_mutating: bool = False
    entity_arg_keys: list[str] = Field(default_factory=list)


class AgentProfile(BaseModel):
    agent_id: str
    agent_type: str
    description: str
    tools: dict[str, ToolCapability]


CUSTOMER_SUPPORT_PROFILE = AgentProfile(
    agent_id="customer_support_v1",
    agent_type="customer_support",
    description="Customer support agent handling orders, customers, deliveries, and notifications.",
    tools={
        "get_order": ToolCapability(
            name="get_order",
            purpose="Retrieve order status and details",
            action_keywords=["find order", "check order", "get order", "where is order", "order status"],
            is_mutating=False,
            entity_arg_keys=["order_id"],
        ),
        "cancel_order": ToolCapability(
            name="cancel_order",
            purpose="Cancel an active order",
            action_keywords=["cancel order", "cancel that order", "cancel"],
            is_mutating=True,
            entity_arg_keys=["order_id"],
        ),
        "get_customer": ToolCapability(
            name="get_customer",
            purpose="Retrieve customer account information",
            action_keywords=["get customer", "find customer", "lookup customer", "check customer"],
            is_mutating=False,
            entity_arg_keys=["customer_id"],
        ),
        "update_customer": ToolCapability(
            name="update_customer",
            purpose="Update customer account details such as email or address",
            action_keywords=["update customer", "modify customer", "change email", "update email"],
            is_mutating=True,
            entity_arg_keys=["customer_id"],
        ),
        "book_delivery": ToolCapability(
            name="book_delivery",
            purpose="Book a delivery time slot for an order",
            action_keywords=["book delivery", "schedule delivery", "book the delivery"],
            is_mutating=True,
            entity_arg_keys=["order_id"],
        ),
        "send_email": ToolCapability(
            name="send_email",
            purpose="Send email confirmation or notification to user",
            action_keywords=["email", "e-mail", "send confirmation", "send the confirmation", "email confirmation"],
            is_mutating=True,
            entity_arg_keys=["order_id", "customer_id"],
        ),
        "search_inventory": ToolCapability(
            name="search_inventory",
            purpose="Search parts and products in catalog inventory",
            action_keywords=["search inventory", "find part", "replacement part", "search catalog"],
            is_mutating=False,
        ),
        "refund_status": ToolCapability(
            name="refund_status",
            purpose="Check the status of a pending refund",
            action_keywords=["refund", "refund status", "check refund"],
            is_mutating=False,
            entity_arg_keys=["order_id"],
        ),
    },
)

CODING_AGENT_PROFILE = AgentProfile(
    agent_id="coding_agent_v1",
    agent_type="coding_agent",
    description="Software engineering agent that explores code, modifies files, and runs tests.",
    tools={
        "search_code": ToolCapability(
            name="search_code",
            purpose="Search codebase for symbols, patterns, or definitions",
            action_keywords=["search code", "find in code", "search for", "locate symbol"],
            is_mutating=False,
        ),
        "read_file": ToolCapability(
            name="read_file",
            purpose="Read the contents of a file from the repository",
            action_keywords=["read file", "inspect file", "view file", "check code"],
            is_mutating=False,
            entity_arg_keys=["file_path", "path"],
        ),
        "write_file": ToolCapability(
            name="write_file",
            purpose="Write or modify code in a file",
            action_keywords=["write file", "edit file", "fix bug", "patch file", "implement", "update code"],
            is_mutating=True,
            entity_arg_keys=["file_path", "path"],
        ),
        "run_tests": ToolCapability(
            name="run_tests",
            purpose="Execute test suite or specific test file",
            action_keywords=["run tests", "run test", "execute tests", "make sure tests pass", "verify tests", "tests pass"],
            is_mutating=False,
        ),
        "git_diff": ToolCapability(
            name="git_diff",
            purpose="Inspect unstaged or staged git changes",
            action_keywords=["git diff", "inspect changes", "check diff", "review diff"],
            is_mutating=False,
        ),
        "run_command": ToolCapability(
            name="run_command",
            purpose="Run a shell or build command in the terminal",
            action_keywords=["run command", "execute command", "build"],
            is_mutating=True,
        ),
    },
)

REGISTRY: dict[str, AgentProfile] = {
    "customer_support": CUSTOMER_SUPPORT_PROFILE,
    "customer_support_v1": CUSTOMER_SUPPORT_PROFILE,
    "coding_agent": CODING_AGENT_PROFILE,
    "coding_agent_v1": CODING_AGENT_PROFILE,
}


def get_agent_profile(agent_type: Optional[str]) -> AgentProfile:
    if not agent_type:
        return CUSTOMER_SUPPORT_PROFILE
    return REGISTRY.get(agent_type, CUSTOMER_SUPPORT_PROFILE)
