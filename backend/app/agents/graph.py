"""
LangGraph interview agent graph.
Wires all nodes together into a stateful workflow.

Graph flow:
  START
    → conversation_manager
    → [route by stage]
        → question_generator → END (wait for user)
        → answer_evaluator → feedback_generator → END (wait for user)
        → interview_complete → END
"""

import logging
from typing import Any, Dict, Literal

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.answer_evaluator import answer_evaluator_node
from app.agents.nodes.conversation_manager import conversation_manager_node
from app.agents.nodes.feedback_generator import feedback_generator_node
from app.agents.nodes.question_generator import question_generator_node
from app.agents.state import InterviewStage

logger = logging.getLogger(__name__)


def route_after_conversation_manager(
    state: Dict[str, Any],
) -> Literal[
    "question_generator",
    "answer_evaluator",
    "interview_complete",
    "wait_for_input",
]:
    """
    Router function: decides which node to go to after conversation_manager.
    This is the central routing logic for the entire interview workflow.
    """
    stage = state.get("interview_stage", InterviewStage.INITIALIZING.value)

    if stage == InterviewStage.GENERATING_QUESTION.value:
        return "question_generator"
    elif stage == InterviewStage.EVALUATING_ANSWER.value:
        return "answer_evaluator"
    elif stage == InterviewStage.INTERVIEW_COMPLETE.value:
        return "interview_complete"
    else:
        # WAITING_FOR_ANSWER or other — end this turn, wait for user input
        return "wait_for_input"


def build_interview_graph() -> StateGraph:
    """
    Build and compile the LangGraph interview workflow.

    Returns:
        Compiled StateGraph ready to invoke
    """
    # Use dict-based state (simpler than TypedDict for our use case)
    graph = StateGraph(dict)

    # Register all nodes
    graph.add_node("conversation_manager", conversation_manager_node)
    graph.add_node("question_generator", question_generator_node)
    graph.add_node("answer_evaluator", answer_evaluator_node)
    graph.add_node("feedback_generator", feedback_generator_node)
    graph.add_node("interview_complete", lambda s: s)  # Pass-through terminal node
    graph.add_node("wait_for_input", lambda s: s)      # Pass-through wait node

    # Entry point
    graph.add_edge(START, "conversation_manager")

    # Conditional routing after conversation_manager
    graph.add_conditional_edges(
        "conversation_manager",
        route_after_conversation_manager,
        {
            "question_generator": "question_generator",
            "answer_evaluator": "answer_evaluator",
            "interview_complete": "interview_complete",
            "wait_for_input": "wait_for_input",
        },
    )

    # After question is generated — end turn, wait for answer
    graph.add_edge("question_generator", END)

    # After answer is evaluated — generate feedback
    graph.add_edge("answer_evaluator", "feedback_generator")

    # After feedback — end turn, wait for user to continue
    graph.add_edge("feedback_generator", END)

    # Terminal nodes
    graph.add_edge("interview_complete", END)
    graph.add_edge("wait_for_input", END)

    compiled = graph.compile()
    logger.info("Interview graph compiled successfully")
    return compiled


# Build the graph once at module load time
interview_graph = build_interview_graph()
