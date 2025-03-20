import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage,HumanMessage
from langgraph.types import interrupt,Command
from typing import Annotated
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph,START,END
import operator
from typing_extensions import TypedDict
from IPython.display import Image, display
from datetime import datetime
from pydantic import BaseModel,Field
from typing_extensions import Annotated,Literal
load_dotenv()

# Setting the env variables
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Calling the LLM model
llm = ChatGroq(model="llama-3.3-70b-versatile",temperature=0.3)

# Defining the overall state for the workflow
class MessageState(TypedDict):
    input: str
    user_feedback: str
    binary_score: str

# Define the Schema Model 
class ScoreModel(BaseModel):
    binary_score:Literal["yes","no"] = Field(description="'yes' for positive response and 'no' for negative response.")

# Generator model
LLMStructure = llm.with_structured_output(ScoreModel)

# Defining the Node functions
def first_node(state:MessageState):
    print("------- FIRST NODE CALLING -------")
    pass

def human_feedback(state:MessageState):
    print("-------- WAITING FOR THE HUMAN FEEDBACK ---------")
    feedback = interrupt("Please provide the feedback : ")
    llm_output = LLMStructure.invoke([SystemMessage(content="You are a sentiment analyzer, Analyse the given feedback. If feedback is positive then return 'yes' else written 'no'.")]+[HumanMessage(content=f"Analyse the given feedback : {feedback}")])
    return {"user_feedback":feedback,"binary_score":llm_output.binary_score}

def route_traffic(state:MessageState):
    if state["binary_score"] == "yes":
        return "second_node"
    elif state["binary_score"] == "no":
        return "first_node"

def second_node(state:MessageState):
    print("------- SECOND NODE CALLING --------")
    pass

# NODES
builder = StateGraph(MessageState)
builder.add_node("first_node",first_node)
builder.add_node("human_feedback",human_feedback)
builder.add_node("second_node",second_node)

# EDGES
builder.add_edge(START,"first_node")
builder.add_edge("first_node","human_feedback")
builder.add_conditional_edges("human_feedback",route_traffic,{"second_node":"second_node","first_node":"first_node"})
builder.add_edge("second_node",END)

# COMPILE
workflow = builder.compile(checkpointer=MemorySaver())

initial_input = {"input":"Hello World"}
config = {"configurable":{"thread_id":datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}}

flag = True
while flag:
    for event in workflow.stream(initial_input, config, stream_mode="updates"):
        if '__interrupt__' in event:
            human_feedback = input("Enter the human feedback")
            workflow.invoke(Command(resume=human_feedback),config,stream_mode="updates")
            if workflow.get_state(config).values["binary_score"] == "yes":
                flag=False
            else:
                flag = True
