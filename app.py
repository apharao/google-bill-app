import streamlit as st
from random import choice

# Initialize session state
if "question_number" not in st.session_state:
    st.session_state.question_number = 1
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.guess_ready = False
    st.session_state.awaiting_response = True

# Question bank
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

# UI layout
st.set_page_config(page_title="🧠 21 Questions AI Guesser", page_icon="🧩")
st.title("🧠 21 Questions - AI Guesses Your Word")
st.markdown("Think of an object. I’ll try to guess it by asking 21 yes/no/maybe questions.")

if st.session_state.question_number <= 21:
    q_idx = st.session_state.question_number - 1
    st.subheader(f"Question {st.session_state.question_number}")
    st.write(f"**{questions[q_idx]}**")

    response = st.radio("Your answer:", ["", "Yes", "No", "Maybe"], key=f"response_{st.session_state.question_number}")

    if st.button("Next"):
        if response == "":
            st.warning("Please select an answer before continuing.")
        else:
            st.session_state.questions.append(questions[q_idx])
            st.session_state.answers.append(response)
            st.session_state.question_number += 1

            if st.session_state.question_number > 21:
                st.session_state.guess_ready = True

            st.experimental_rerun()

else:
    st.success("I've asked 21 questions. Time to guess your word!")

if st.session_state.get("guess_ready", False):
    sample_guesses = ["A phone", "A cat", "A book", "A jacket", "A blender", "A tree", "A television", "A backpack"]
    st.subheader("🤔 My Guess Is...")
    st.header(choice(sample_guesses))

    if st.button("Start Over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()
