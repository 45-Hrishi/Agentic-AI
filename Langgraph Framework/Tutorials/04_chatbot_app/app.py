import streamlit as st
from bot import Chatbot

mybot = Chatbot()
workflow = mybot()


st.title("Chatbot using LangGraph")
st.write("Ask any question, and I will try to answer it!")

question = st.text_input("Enter your question here!")
input = {"messages":[question]}

if st.button("Get answer"):
    if input:
        response = workflow.invoke(input)
        st.write("**Answer: **",response["messages"][-1].content)
    else:
        st.warning("Please ask question to get answer")