from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.tools import GoogleSearchAPIWrapper

def create_research_chain():
    """
    Creates an LLMChain with conversational memory and web search capability.

    This function sets up a conversational agent that can remember past interactions
    and perform web searches to retrieve the latest research information.

    Returns:
        LLMChain: A chain object that processes user input, maintains conversation history,
                  and fetches web search results.
    """
    # Define the prompt template with placeholders for chat history and user input
    template = """You are a research assistant chatbot having a conversation with a human.

    {chat_history}
    Human: {human_input}
    Chatbot:"""

    # Initialize the prompt with the specified input variables and template
    prompt = PromptTemplate(
        input_variables=["chat_history", "human_input"], template=template
    )

    # Initialize the conversation memory to keep track of the chat history
    memory = ConversationBufferMemory(memory_key="chat_history")

    # Initialize the language model (LLM) you want to use (e.g., OpenAI's GPT-3)
    llm = OpenAI()

    # Initialize the web search tool (e.g., Google Search)
    search = GoogleSearchAPIWrapper()

    # Create the LLMChain with the LLM, prompt, memory, and web search tool
    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        tools=[search],  # Add the search tool to the chain
        verbose=True,
    )

    return llm_chain

# Example usage
if __name__ == "__main__":
    # Create the research chain
    research_chain = create_research_chain()

    # User input
    user_input = "Can you provide the latest research on quantum computing?"

    # Get the chatbot's response
    response = research_chain.run(human_input=user_input)

    # Print the response
    print(response)
