# Required Libs
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from pymongo import MongoClient
import datetime
import ollama
import streamlit as st
import hashlib

# Streamlit webpage Setup
st.set_page_config(page_title="HR Buddy", page_icon="🤖")
st.title("HR Policy Assistant")

# Cached Setup for loading model and the database
# Runs only once

@st.cache_resource
def initialize_backend():

    print("\n[INFO] Booting up HR Buddy Server...")
    
    # Connecting to default local MongoDB Port
    print("[INFO] Connecting to local MongoDB...")
    client = MongoClient("mongodb://localhost:27017/")

    # Retrieve Memory Database
    db = client["hr_assistant"]
    chat_collection = db["chat_history"]
    users_collection = db["users"]
    
    # Load and Chunk the Data
    print("[INFO] Reading HR Policy PDF with PyMuPDF...")
    loader = PyMuPDFLoader("rag_source/nasscom-hr-manual-2016.pdf") 
    pages = loader.load()

    # Break the dense PDF into small, 1000-character chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(pages)
    
    print(f"[INFO] PDF chunked successfully into {len(chunks)} segments.")
    print("[INFO] Initializing vector embeddings. This might take a second...")

    # Embed and Store in Vector DB
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    
    print("[SUCCESS] System is live and ready for users!\n")
    return chat_collection, retriever, users_collection

chat_collection, retriever, users_collection = initialize_backend()

# User login
# Set up empty variables in Streamlit's memory
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.session_id = ""

if not st.session_state.logged_in:
    st.sidebar.subheader("🔒 Login or Register")
    username_input = st.sidebar.text_input("Username:")
    password_input = st.sidebar.text_input("Password:", type="password") 
    
    if st.sidebar.button("Enter"):
        if username_input and password_input:
            # Scramble the password into a secure hash
            pwd_hash = hashlib.sha256(password_input.encode()).hexdigest()
            
            # Look for the user in MongoDB
            user_record = users_collection.find_one({"username": username_input})
            
            if user_record:
                # User exists: Check if hashes match
                if user_record["password_hash"] == pwd_hash:
                    st.session_state.logged_in = True
                    st.session_state.session_id = username_input
                    st.rerun() 
                    
                else:
                    st.sidebar.error("Incorrect password!")
            else:
                # 4. User does not exist: Register them silently
                users_collection.insert_one({"username": username_input, "password_hash": pwd_hash})
                st.sidebar.success("New account created!")
                st.session_state.logged_in = True
                st.session_state.session_id = username_input
                st.rerun()
        else:
            st.sidebar.warning("Please enter both username and password.")
            
    
    st.stop() 

else:
    # If we get here, the user is successfully logged in!
    SESSION_ID = st.session_state.session_id
    st.sidebar.success(f"Logged in as: **{SESSION_ID}**")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# If - Login is successful
# Fetch chat history for the UI
if "messages" not in st.session_state:
    st.session_state.messages = []

    # Pull previous messages from MongoDB to show on screen
    past_db_msgs = chat_collection.find({"session_id": SESSION_ID}).sort("timestamp", 1)
    for msg in past_db_msgs:
        st.session_state.messages.append({
            "role": "user" if msg["role"] == "User" else "assistant", 
            "content": msg["content"]
        })

# Display all messages on the screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask a question about HR policies..."):

    # Print log about chat on terminal
    print(f"\n[USER:{SESSION_ID}] New question received: '{user_input}'")

    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Prepare Context & History
    print(f"[SYSTEM] Fetching RAG context and database memory for {SESSION_ID}...")

    # Semantic Search: Find the relevant policy paragraphs from the RAG source
    docs = retriever.invoke(user_input)
    context_block = "\n\n".join([doc.page_content for doc in docs])
    
    # Get last 10 messages from the user
    past_messages = chat_collection.find({"session_id": SESSION_ID}).sort("timestamp", -1).limit(10)

    # Convert cursor to list and reverse for reading it from start to end
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in list(past_messages)[::-1]])
    
    # Construct the Prompt with Attention
    # Custom RAG Prompt to only use resources from the rag source
    rag_prompt = f"""You are a helpful, polite, and precise HR assistant. You are currently speaking with an employee named {SESSION_ID}.
    
    RULES:
    1. For greetings, casual conversation, or identity questions, respond naturally.
    2. For ANY question regarding company policy, you MUST answer using ONLY the facts found in the Context below.
    3. If the exact answer is not in the Context, reply: "I cannot find the answer to that in the current policy."
    
    --- PAST MEMORY ---
    {history_text}
    
    --- HR CONTEXT --- 
    {context_block}
    
    Question: {user_input}
    Answer:"""

    # Generate and show AI response
    print("[SYSTEM] Sending prompt to Llama 3.2...")
    with st.chat_message("assistant"):

        # Generate the answer using Llama 3.2
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': rag_prompt}])
        ai_answer = response['message']['content']
        st.markdown(ai_answer)
        
    st.session_state.messages.append({"role": "assistant", "content": ai_answer})
    
    # Save to MongoDB
    chat_collection.insert_many([
        {"session_id": SESSION_ID, "role": "User", "content": user_input, "timestamp": datetime.datetime.now(datetime.timezone.utc)},
        {"session_id": SESSION_ID, "role": "AI", "content": ai_answer, "timestamp": datetime.datetime.now(datetime.timezone.utc)}
    ])
    
    # Terminal Log after AI gives output
    print(f"[SUCCESS] AI responded and conversation saved to MongoDB for {SESSION_ID}.")
