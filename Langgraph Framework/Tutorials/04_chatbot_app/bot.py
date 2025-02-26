import os
from dotenv import load_dotenv
from langgraph.graph import MessagesState,StateGraph,Graph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated, Literal, TypedDict
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_community.tools import TavilySearchResults
from langchain_groq import ChatGroq
load_dotenv()

os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

class Chatbot:
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.3-70b-versatile",temperature=0)
    
    # Tool  
    def call_tool(self):
        tool = TavilySearchResults(max_results=2)
        tools = [tool]
        self.tool_node = ToolNode(tools)
        self.llm_with_tools = self.llm.bind_tools(tools)
        
    # Agent
    def call_model(self,state:MessagesState):
        messages = state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages":[response]}
    
    # Router
    def router_function(self,state:MessagesState) -> Literal["tools",END]:
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END
    
    
    def __call__(self):
        self.call_tool()
        workflow = StateGraph(MessagesState)
        workflow.add_node("agent",self.call_model)
        workflow.add_node("tools",self.tool_node)
        workflow.add_edge(START,"agent")
        workflow.add_conditional_edges("agent",self.router_function,{"tools":"tools",END:END})
        workflow.add_edge("tools","agent")
        self.app = workflow.compile()
        return self.app
    
if __name__ == "__main__":
    mybot = Chatbot()
    workflow = mybot()
    response = workflow.invoke({"messages":["Who is the current precident of India"]})
    print(response["messages"][-1].content)