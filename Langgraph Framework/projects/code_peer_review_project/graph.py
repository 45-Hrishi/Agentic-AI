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
from langgraph.constants import Send
from IPython.display import Markdown
load_dotenv()

# Setting the env variables
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Calling the LLM model
llm = ChatGroq(model="llama-3.3-70b-versatile",temperature=0.3)

# Defining the overall state for the workflow
class MessageState(TypedDict):
    input: str
    user_feedback: str

# Define the Schema Model 
class ScoreModel(BaseModel):
    binary_score:Literal["yes","no"] = Field(description="'yes' for positive response and 'no' for negative response.")

# Generator model
LLMStructure = llm.with_structured_output(ScoreModel)

# Defining the Node functions
def first_node(state:MessageState):
    print("------- FIRST NODE CALLING -------")
    pass

def second_node(state:MessageState):
    print("------- SECOND NODE CALLING --------")
    pass

def human_feedback(state:MessageState):
    print("-------- IN HUMAN FEEDBACK NODE ---------")
    feedback = interrupt("Please provide the feedback (Use True to continue the workflow): ")
    
    if isinstance(feedback, bool) and feedback is True:
        return Command(goto=[Send(node="third_node", arg={"user_feedback":feedback})])
    
    elif isinstance(feedback, str):
        return Command(goto="second_node",update={"user_feedback": feedback})
    else:
        raise TypeError(f"Interrupt value of type {type(feedback)} is not supported.")

def route_traffic(state:MessageState):
    if state["binary_score"] == "yes":
        return "third_node"
    elif state["binary_score"] == "no":
        return "second_node"

def third_node(state:MessageState):
    print("------- THIRD NODE CALLING --------")
    print("User feedback is : ",state["user_feedback"])
    pass

# NODES
builder = StateGraph(MessageState)
builder.add_node("first_node",first_node)
builder.add_node("second_node",second_node)
builder.add_node("human_feedback",human_feedback)
builder.add_node("third_node",third_node)

# EDGES
builder.add_edge(START,"first_node")
builder.add_edge("first_node","second_node")
builder.add_edge("second_node","human_feedback")
# builder.add_conditional_edges("human_feedback",route_traffic,{"second_node":"second_node","third_node":"third_node"})
builder.add_edge("third_node",END)


# COMPILE
workflow = builder.compile(checkpointer=MemorySaver())

initial_input = {"input":"Hello World"}
config = {"configurable":{"thread_id":datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}}

# flag = True
# while flag:
#     for event in workflow.stream(initial_input, config, stream_mode="updates"):
#         if '__interrupt__' in event:
#             human_feedback = input("Enter the human feedback")
#             workflow.invoke(Command(goto=),config,stream_mode="updates")
#             if workflow.get_state(config).values["binary_score"] == "yes":
#                 flag=False
#             else:
#                 flag = True

# for event in workflow.stream(initial_input, config, stream_mode="updates"):
#     if '__interrupt__' in event:
#         interrupt_value = event['__interrupt__'][0].value
#         # display(Markdown(interrupt_value))
#         print(interrupt_value)
        
# for event in workflow.stream(Command(resume="Bad code, disgusting"),config,stream_mode="updates"):
#     if '__interrupt__' in event:
#         interrupt_value2 = event['__interrupt__'][0].value
#         # display(Markdown(interrupt_value))    
#         print(interrupt_value2)
        
# for event in workflow.stream(Command(resume=True),config,stream_mode="updates"):
#     if '__interrupt__' in event:
#         interrupt_value3 = event['__interrupt__'][0].value
#         # display(Markdown(interrupt_value))    
#         print(interrupt_value3)
# Single loop to handle streaming and interrupts

current_command = None  # To track resume command state

while True:
    stream = workflow.stream(initial_input if current_command is None else current_command, config, stream_mode="updates")
    interrupt_received = False

    for event in stream:
        if '__interrupt__' in event:
            interrupt_value = event['__interrupt__'][0].value
            print(interrupt_value)

            # Get user input for resume
            user_input = input(">>> Enter feedback (text or True): ")

            # Interpret input
            if user_input.lower() == "true":
                current_command = Command(resume=True)
            else:
                current_command = Command(resume=user_input)
            
            interrupt_received = True
            break  # Break the current stream loop and restart with new resume command

    if not interrupt_received:
        break  # Exit loop when there’s no more interrupt