from langgraph.types import interrupt,Command
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from typing_extensions import Literal

# Graph state
class State(TypedDict):
    joke: str
    topic: str
    llm_feedback: str
    human_feedback: str
    funny_or_not: str
    human_grade:str


# Schema for structured output to use in evaluation
class Feedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(
        description="Decide if the joke is funny or not.",
    )
    feedback: str = Field(
        description="If the joke is not funny, provide feedback on how to improve it.",
    )


# Schema for structured output to use in human feedback evaluation
class HumanFeedback(BaseModel):
    grade: Literal["funny","not funny"] = Field(
        description="Based on provided feedback, decide joke is funny or not funny",
    )


# LangGraph graph
class PracticeGraph:
    def __init__(self,model_name,temperature=0):
        self.model = model_name
        self.llm = ChatGroq(model=self.model,temperature=temperature)
        self.memory = MemorySaver()
        self.evaluator = self.llm.with_structured_output(Feedback)
        self.human_evaluator = self.llm.with_structured_output(HumanFeedback)
    
    
    # Define the nodes of the graph
    def llm_call_generator(self,state: State):
        """LLM generates a joke"""

        if state.get("llm_feedback") or state.get("human_feedback"):
            msg = self.llm.invoke(
                f"Write a joke about {state['topic']} but take into account the LLM feedback {state['llm_feedback']} and human feedback {state['human_feedback']}"
            )
        else:
            msg = self.llm.invoke(f"Write a joke about {state['topic']}")
        return {"joke": msg.content}


    def llm_call_evaluator(self,state: State):
        """LLM evaluates the joke"""
        grade = self.evaluator.invoke(f"Grade the joke {state['joke']}")
        return {"funny_or_not": grade.grade,"llm_feedback":grade.feedback}


    def human_feedback(self,state:State):
        """Get the feedback from human"""
        human_feedback = interrupt("Hey! Do you feel it funny or not ?")
        state['human_feedback'] = human_feedback
        grade = self.human_evaluator.invoke(f"Grade the human feedback {human_feedback}")
        return {"human_feedback":human_feedback, "human_grade":grade.grade}
    
    
    # Conditional edge function to route back to joke generator or end based upon feedback from the evaluator
    def route_joke(self,state: State):
        """Route back to joke generator or end based upon feedback from the evaluator"""

        if state["funny_or_not"] == "funny" and state["human_grade"] == "funny":
            return "Accepted"
        elif state["funny_or_not"] == "not funny" and state["human_grade"] == "not funny":
            return "Rejected + Feedback"
        elif state["funny_or_not"] == "funny" and state["human_grade"] == "not funny":
            return "Rejected + Feedback"
        elif state["funny_or_not"] == "not funny" and state["human_grade"] == "funny":
            return "Accepted"
        
    
    def build_graph(self):
        optimizer_builder = StateGraph(State)

        # Add the nodes
        optimizer_builder.add_node("llm_call_generator", self.llm_call_generator)
        optimizer_builder.add_node("llm_call_evaluator", self.llm_call_evaluator)
        optimizer_builder.add_node("human_feedback_evaluator", self.human_feedback)

        # Add edges to connect nodes
        optimizer_builder.add_edge(START, "llm_call_generator")
        optimizer_builder.add_edge("llm_call_generator", "llm_call_evaluator")
        optimizer_builder.add_edge("llm_call_evaluator", "human_feedback_evaluator")

        optimizer_builder.add_conditional_edges(
            "human_feedback_evaluator",
            self.route_joke,
            {  # Name returned by route_joke : Name of next node to visit
                "Accepted": END,
                "Rejected + Feedback": "llm_call_generator",
            },
        )

        # Compile the workflow
        optimizer_workflow = optimizer_builder.compile(checkpointer=self.memory)
        return optimizer_workflow