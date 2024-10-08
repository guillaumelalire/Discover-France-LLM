import streamlit as st
import random
import time
from rag import create_vector_storage, launch_model, llm_response
from audio import extract_audio, transcript, translate_to_english

VIDEO_FILEPATH = "video.mp4"
AUDIO_FILEPATH = "audio.mp3"

if 'stage' not in st.session_state:
    st.session_state.stage = 0

def change_stage(stage):
    st.session_state.stage = stage

st.title("Chat with Video:clapper:")

if st.session_state.stage == 0:
    form = st.form("my_form")
    uploaded_file = form.file_uploader("Choose a local file", accept_multiple_files=False)
    youtube_link = form.text_input(
        "or provide the link to a YouTube video",
        "",
    )
    submit = form.form_submit_button()
    if (uploaded_file or youtube_link) and submit:
        if uploaded_file and uploaded_file:
            with open(VIDEO_FILEPATH, 'wb') as f:
                f.write(uploaded_file.getvalue())
            st.session_state.uploaded_file = VIDEO_FILEPATH
        else:
            st.session_state.uploaded_file = ""
        st.session_state.youtube_link = youtube_link
        change_stage(1)

if st.session_state.stage == 1:
    with st.status("Processing video...", expanded=True) as status:
        try:
            st.write("Extracting audio...")
            st.session_state.video_name = extract_audio(st.session_state.uploaded_file, st.session_state.youtube_link, AUDIO_FILEPATH)
            if uploaded_file:
                st.session_state.video_name = uploaded_file.name
    
            st.write("Transcribing...")
            transcription, language = transcript(AUDIO_FILEPATH)
        except:
            change_stage(0)
            raise ValueError("Invalid file or YouTube link.")

        if language != "en":
            st.write("Translating transcription...")
            transcription = translate_to_english(transcription, language)
        
        st.session_state.transcription = transcription
        
        st.write("Creating vector database...")
        db = create_vector_storage(transcription)
        
        st.write("Launching LLM...")
        st.session_state.rag_chain = launch_model(db)
        
        status.update(label=f"Processing of **{st.session_state.video_name}** complete!", state="complete", expanded=False)
    change_stage(2)

if st.session_state.stage == 3:
    st.status(label=f"Processing of **{st.session_state.video_name}** complete!", state="complete", expanded=False)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Streamed response emulator
def generate_response(prompt):
    response = llm_response(st.session_state.rag_chain, prompt)
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.05)

# Accept user input
if st.session_state.stage > 0:  
    change_stage(3)
    prompt = st.chat_input("What is up?")
    if prompt:
    # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
    # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = st.write_stream(generate_response(prompt))
    
    # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})