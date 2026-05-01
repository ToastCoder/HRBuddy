import streamlit as st
import hashlib
import datetime
from pymongo import MongoClient

# --- MODULAR IMPORTS ---
from core.config_loader import cfg
from core.logger import log
from core.ingestion import process_pdf
from core.rag_engine import HRBuddyEngine

# Setup page using JSON configuration
st.set_page_config(page_title=cfg.get("app_name", "HR Buddy"), layout="wide")
st.title(cfg.get("app_name", "HR Policy Assistant"))

# --- BACKEND INITIALIZATION ---
@st.cache_resource
def initialize_system():
    log.info(f"System boot sequence initiated for {cfg['app_name']}...")
    
    # 1. Connect to MongoDB (URI from JSON)
    client = MongoClient(cfg["vector_store"]["uri"])
    db = client[cfg.get("db_name", "hr_buddy_db")]
    
    # 2. Process PDF (Path from JSON)
    PDF_PATH = cfg["ingestion"]["pdf_path"]
    chunks = process_pdf(PDF_PATH)
    
    # 3. Initialize RAG Engine
    engine = HRBuddyEngine(chunks)
    
    return db["chat_history"], db["users"], engine

chat_collection, users_collection, engine = initialize_system()

# --- LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.subheader("🔒 Authentication")
    user = st.sidebar.text_input("Username")
    pwd = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login/Register"):
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
        user_record = users_collection.find_one({"username": user})
        
        if user_record:
            if user_record["password_hash"] == pwd_hash:
                st.session_state.logged_in = True
                st.session_state.user_id = user
                st.rerun()
            else:
                st.sidebar.error("Invalid password")
        else:
            users_collection.insert_one({"username": user, "password_hash": pwd_hash})
            st.session_state.logged_in = True
            st.session_state.user_id = user
            st.rerun()
    st.stop()

# --- MAIN CHAT INTERFACE ---
SESSION_ID = st.session_state.user_id
st.sidebar.success(f"Active Session: {SESSION_ID}")

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Sync with MongoDB
    past_msgs = chat_collection.find({"session_id": SESSION_ID}).sort("timestamp", 1)
    for m in past_msgs:
        role = "user" if m["role"] == "User" else "assistant"
        st.session_state.messages.append({"role": role, "content": m["content"]})

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if user_input := st.chat_input("Ask about company policy..."):
    log.info(f"User Query: {user_input}")
    
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get Chat History for Context (Last 5 messages)
    history_cursor = chat_collection.find({"session_id": SESSION_ID}).sort("timestamp", -1).limit(5)
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in list(history_cursor)[::-1]])

    # Execute RAG Engine
    with st.chat_message("assistant"):
        stream = engine.generate_response(user_input, history_text, SESSION_ID)
        
        def stream_parser(s):
            for chunk in s:
                yield chunk['message']['content']
        
        ai_response = st.write_stream(stream_parser(stream))
    
    st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # Save to Mongo
    chat_collection.insert_many([
        {"session_id": SESSION_ID, "role": "User", "content": user_input, "timestamp": datetime.datetime.now()},
        {"session_id": SESSION_ID, "role": "AI", "content": ai_response, "timestamp": datetime.datetime.now()}
    ])