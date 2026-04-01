# Required Libs
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from pymongo import MongoClient
import datetime
import ollama

# MongoDB Setup
print("[INFO] Connecting to MongoDB...")
try:
    # Connecting to default local MongoDB Port
    mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)

    # Forcing a connection test
    mongo_client.server_info()
    db = mongo_client["hr_assistant"]
    chat_collection = db["chat_history"]
    print("[OK] Connected to MongoDB!")
except Exception as e:
    print("[ERROR] Could not connect to MongoDB. Is the server running?")
    exit(1)

# Dynamic Session ID for handling users and their past questions
print("\nWelcome to HR Buddy")
SESSION_ID = input("Please enter your name to login: ").strip()

# Fallback support as a guest session
if not SESSION_ID:
    SESSION_ID = "guest_user"
    print("[INFO] No name provided. Logging in as 'guest_user'.")
else:
    print(f"[INFO] Hello, {SESSION_ID}! Fetching your records...")


# Load and Chunk the Data
print("[INFO] Reading HR Policy PDF...")
loader = PyMuPDFLoader("rag_source/nasscom-hr-manual-2016.pdf") 
pages = loader.load()

# Break the dense PDF into small, 500-character chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
chunks = text_splitter.split_documents(pages)

# Embed and Store in Vector DB
print(f"[INFO] Chunking complete. Found {len(chunks)} text chunks.")
print("[INFO] Sending chunks to Ollama to create embeddings...")
# fast, local nomic model to turn text into math
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings)

# Retriever to fetch the top 3 most relevant chunks
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

print("\n\nHi there! (Press Ctrl+C to exit)")

# Infinite Loop for Model Input to Output
try:
    while True:
        user_input = input("\n:> ")
        
        # Get last 10 messages from the user
        past_messages_cursor = chat_collection.find({"session_id": SESSION_ID}).sort("timestamp", -1).limit(10)

        # Convert cursor to list and reverse for reading it from start to end
        past_messages = list(past_messages_cursor)[::-1]
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in past_messages])

        # Semantic Search: Find the relevant policy paragraphs from the RAG source
        docs = retriever.invoke(user_input)
        context_block = "\n\n".join([doc.page_content for doc in docs])
        
        # Construct the Prompt with Attention
        # Custom RAG Prompt to only use resources from the rag source
        rag_prompt = f"""You are a precise HR assistant. 
        Read the provided Context carefully. You must answer the user's question using ONLY the facts found in the Context below. 
        
        If the Context does not contain the exact answer, simply reply: "I cannot find the answer to that in the current policy."
        
        --- PAST CONVERSATION MEMORY ---
        {history_text}
        
        --- CURRENT HR CONTEXT --- 
        {context_block}
        
        --- CURRENT QUESTION ---
        Question: {user_input}
        Answer:"""
        
        # Generate the answer using Llama 3.2
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': rag_prompt}
        ])
        
        ai_answer = response['message']['content']
        print(f"\nAI: {ai_answer}")

        chat_collection.insert_many([
            {"session_id": SESSION_ID, "role": "User", "content": user_input, "timestamp": datetime.datetime.now(datetime.timezone.utc)},
            {"session_id": SESSION_ID, "role": "AI", "content": ai_answer, "timestamp": datetime.datetime.now(datetime.timezone.utc)}
        ])

except KeyboardInterrupt:
    print("\n\n[INFO] Closing Chat.")

