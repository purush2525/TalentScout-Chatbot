import streamlit as st
from dotenv import load_dotenv
from core.logic import HiringAssistant
from core.storage import CandidateStore
from core.privacy import mask_contact

load_dotenv()

st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🧭", layout="centered")

if "assistant" not in st.session_state:
    store = CandidateStore(path="data/candidates.jsonl")
    st.session_state.assistant = HiringAssistant(store=store)

assistant = st.session_state.assistant

st.title("🧭 TalentScout – Hiring Assistant")
st.caption("Initial screening chatbot for technology roles")

for role, content in assistant.history:
    with st.chat_message(role):
        st.markdown(content)

if not assistant.history:
    greeting = assistant.greet()
    with st.chat_message("assistant"):
        st.markdown(greeting)
    assistant.append("assistant", greeting)

user_input = st.chat_input("Type your message")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    assistant.append("user", user_input)

    reply = assistant.step(user_input)
    with st.chat_message("assistant"):
        st.markdown(reply)
    assistant.append("assistant", reply)

    if assistant.done:
        rec = assistant.current_record()
        rec["email_masked"] = mask_contact(rec.get("email", ""))
        rec["phone_masked"] = mask_contact(rec.get("phone", ""))
        assistant.store.write(rec)
        st.success("Conversation saved. Thank you.")
        st.balloons()
        if st.button("Start a new conversation"):
            st.session_state.clear()
            st.rerun()
