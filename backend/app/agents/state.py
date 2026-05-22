"""
LangGraph state definition for the interview agent.
The AgentState is passed between all nodes in the graph.
Every field is updated as the interview progresses.
"""

from enum import Enum
from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class InterviewStage(str, Enum):
    """
    The current stage of the interview workflow.
    The LangGraph router uses this to decide which node to call next.
    """
    INITIALIZING = "initializing"
    GENERATING_QUESTION = "generating_question"
    WAITING_FOR_ANSWER = "waiting_for_answer"
    EVALUATING_ANSWER = "evaluating_answer"
    GENERATING_FEEDBACK = "generating_feedback"
    NEXT_QUESTION = "next_question"
    INTERVIEW_COMPLETE = "interview_complete"
    ERROR = "error"


class QuestionRecord(BaseModel):
    """A single interview question with its answer and evaluation."""
    question_id: int
    question: str
    category: str
    difficulty: str
    answer: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)


class AgentState(BaseModel):
    """
    Full state of the interview agent.
    Passed between every LangGraph node.
    All fields are optional with defaults so nodes only update what they need.
    """

    # Session info
    session_id: str = ""
    candidate_name: str = "Candidate"

    # Document context from RAG
    resume_context: str = ""
    jd_context: str = ""
    combined_context: str = ""

    # Interview configuration
    total_questions: int = 5
    current_question_number: int = 0
    interview_stage: InterviewStage = InterviewStage.INITIALIZING

    # Current question being asked
    current_question: Optional[QuestionRecord] = None

    # Full history of Q&A
    questions_asked: List[QuestionRecord] = Field(default_factory=list)

    # Conversation messages (LangGraph managed)
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)

    # Current answer from candidate
    current_answer: str = ""

    # Overall interview metrics
    total_score: float = 0.0
    average_score: float = 0.0

    # Final summary
    final_feedback: str = ""
    overall_assessment: str = ""

    # Error handling
    error_message: str = ""

    # Categories to cover
    question_categories: List[str] = Field(
        default_factory=lambda: [
            "technical_skills",
            "experience",
            "problem_solving",
            "behavioral",
            "cultural_fit",
        ]
    )

    class Config:
        arbitrary_types_allowed = True
