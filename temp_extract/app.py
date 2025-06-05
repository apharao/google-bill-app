import streamlit as st

# Setup session state
if "question_number" not in st.session_state:
    st.session_state.question_number = 1
    st.session_state.answers = []

# 21 Questions Prompt
questions = [
    "What’s your favorite movie?",
    "If you could live anywhere in the world, where would it be?",
    "What’s your biggest fear?",
    "Do you believe in fate or free will?",
    "What’s a secret talent you have?",
    "What’s something you’ve always wanted to learn?",
    "What’s the most spontaneous thing you’ve ever done?",
    "What’s a memory that always makes you smile?",
    "If you could have dinner with anyone (dead or alive), who would it be?",
    "What’s your guilty pleasure?",
    "What’s something most people don’t know about you?",
    "What’s the best compliment you’ve ever received?",
    "If you could have any superpower, what would it be?",
    "What’s your favorite childhood memory?",
    "What motivates you to keep going on tough days?",
    "What’s a goal you’re currently working on?",
    "What’s a book or movie that changed your perspective?",
    "Do you believe people can change?",
    "What’s a value you will never compromise on?",
    "If money wasn’t an issue, how would you spend your days?",
    "What does happiness mean to you?"
]

st.set_page_config(page_title="21 Questions Game", page_icon="❓")
st.title("🎲 21 Questions Game")
st.markdown("Answer a series of questions and learn more about yourself or your friends!")

# Display question
q_index = st.session_state.question_number - 1
if q_index < len(questions):
    st.subheader(f"Question {st.session_state.question_number}")
    answer = st.text_input(questions[q_index], key=f"q{q_index}")

    if st.button("Next"):
        if answer.strip() == "":
            st.warning("Please enter an answer before continuing.")
        else:
            st.session_state.answers.append(answer.strip())
            st.session_state.question_number += 1
            st.experimental_rerun()
else:
    st.success("🎉 You've completed all 21 questions!")
    st.subheader("Your Answers:")
    for i, a in enumerate(st.session_state.answers, start=1):
        st.write(f"**{i}.** {a}")

    if st.button("Restart"):
        st.session_state.question_number = 1
        st.session_state.answers = []
        st.experimental_rerun()
