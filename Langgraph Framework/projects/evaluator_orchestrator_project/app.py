from graph import PracticeGraph
from datetime import datetime
import streamlit as st
from langgraph.types import Command

graph = PracticeGraph(model_name="llama-3.2-11b-vision-preview")
workflow = graph.build_graph()

# -------------- Streamlit UI ----------------
st.title("LangGraph Chatbot with Human Feedback")

# Initialize session state
# if "state" not in st.session_state:
#     st.session_state.state = {
#         "topic": "",
#         "joke": "",
#         "llm_feedback": "",
#         "human_feedback": "",
#         "funny_or_not": "",
#         "human_grade": "",
#     }
if "config" not in st.session_state:
    st.session_state.config = {}
if "show_feedback_popup" not in st.session_state:
    st.session_state.show_feedback_popup = False
if "feedback_mesg" not in st.session_state:  
    st.session_state.feedback_mesg = ""
    
# User input for chatbot question
user_input = st.text_input("Ask a question:")

if st.button("Submit") and user_input:
    # Generate a thread ID based on the current timestamp
    st.session_state.config = {"configurable": {"thread_id": datetime.now().strftime("%Y%m%d%H%M%S%f")}}

    response = workflow.invoke(
        {"topic": user_input}, 
        config=st.session_state.config, 
        stream_mode="updates"
    )
    st.session_state.show_feedback_popup = True  # Trigger feedback popup


    # Display chatbot response
    if response:
        for item in response:
            if 'llm_call_generator' in item:
                joke_data = item['llm_call_generator']
        joke = joke_data.get('joke','No joke found')
        st.write("🤖 Chatbot Response:", joke)
        
        # Extract human feedback interrupt message
    
        for item in response:
            if '__interrupt__' in item:
                interrupt_msg = item.get("__interrupt__")[0].value

    if st.session_state.get("show_feedback_popup", False):
        st.session_state.feedback_mesg = st.text_input(
            label="Your feedback:",
            placeholder="Give feedback",
            value=st.session_state.feedback_mesg  # Keep the value persistent
        )

        if st.button("Send Feedback", key="feedback"): 
            print("Feedback Message:", st.session_state.feedback_mesg)
            print("Config:", st.session_state.config)

            # Resume workflow with feedback
            response = workflow.invoke(
                Command(resume=st.session_state.feedback_mesg),
                config=st.session_state.config,
                stream_mode="values"
            )
            print("Response:", response)
                # Extract human evaluation result
            # human_eval_data = next((item['human_feedback_evaluator'] for item in st.session_state.state if 'human_feedback_evaluator' in item), {})
            # human_grade = human_eval_data.get('human_grade', 'unknown')
                
            #     # Stop flow if both agree it's funny
            # if human_grade == "funny":
            #         st.session_state.show_feedback_popup = False
            #         st.success("Feedback received! Joke is funny. No further processing.")
            # else:
            #         st.warning("Feedback received! Generating a better joke...")
                
                
        
