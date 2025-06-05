import streamlit as st
from random import choice

# Setup session state
if "question_number" not in st.session_state:
    st.session_state.question_number = 1
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.guess_ready = False

questions = [
    "Is it a living thing?",
    "Can it be found indoors?",
    "Is it man-made?",
    "Is it larger than a microwave?",
    "Is it something you use every day?",
    "Does it require electricity?",
    "Can you eat it?",
    "Is it used for entertainment?",
    "Is it found in nature?",
    "Can it be bought in a store?",
    "Is it commonly used in work or school?",
    "Is it associated with a specific color?",
    "Is it soft to the touch?",
    "Can it be worn?",
    "Does it move on its own?",
    "Is it considered expensive?",
    "Is it associated with a specific season?",
    "Would you give it as a gift?",
    "Is it used by children?",
    "Does it produce sound?",
    "Would you find it in a car?"
]

st.set_page_config(page_title="🧠 21 Questions AI Guesser", page_icon="🎯")
st.title("🧠 21 Questions - AI Guesses Your Word")
st.markdown("Think of an object and I’ll try to guess it by asking up to 21 questions.")

# Proceed only if fewer than 21 questions answered
if st.session_state.question_number <= 21:
    q_num = st.session_state.question_number
    question = questions[q_num - 1]

    st.subheader(f"Question {q_num}")
    st.markdown(f"**{question}**")

    selected = st.radio("Your answer:", ["Yes", "No", "Maybe"], key=f"answer_{q_num}")

    if st.button("Submit Answer"):
        st.session_state.questions.append(question)
        st.session_state.answers.append(selected)
        st.session_state.question_number += 1

        if st.session_state.question_number > 21:
            st.session_state.guess_ready = True

else:
    st.success("I've asked 21 questions. Time to guess your word!")

if st.session_state.get("guess_ready", False):
    guesses = ["A phone", "A cat", "A book", "A jacket", "A blender", "A tree", "A television", "A backpack"]
    st.subheader("🤔 My Guess Is...")
    st.header(choice(guesses))

    if st.button("Start Over"):
        st.session_state.clear()
