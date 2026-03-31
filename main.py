# Required Libs
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
import ollama

# Load and Chunk the Data
print("[INFO] Reading HR Policy PDF...")
loader = PyPDFLoader("rag_source/nasscom-hr-manual-2016.pdf") 
pages = loader.load()

# Break the dense PDF into small, 500-character chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(pages)

# Embed and Store in Vector DB
print("[INFO] Embedding text and building Chroma database...")
# fast, local nomic model to turn text into math
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings)

# Retriever to fetch the top 3 most relevant chunks
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

print("\n\nHi there! (Press Ctrl+C to exit)")

# Infinite Loop for Model Input to Output
try:
    while True:
        user_input = input("\n:> ")
        
        # Semantic Search: Find the relevant policy paragraphs
        docs = retriever.invoke(user_input)
        context_block = "\n\n".join([doc.page_content for doc in docs])
        
        # Construct the Prompt with Attention
        # Custom RAG Prompt to only use resources from the rag source
        rag_prompt = f"""You are a helpful HR assistant. Answer the user's question using ONLY the context provided below. If the answer is not in the context, say you don't know.
        
        Context: 
        {context_block}
        
        Question: {user_input}
        Answer:"""
        
        # C. Generate the answer using TinyLlama
        response = ollama.chat(model='tinyllama', messages=[
            {'role': 'user', 'content': rag_prompt}
        ])
        
        print(f"\nAI: {response['message']['content']}")

except KeyboardInterrupt:
    print("\n\n[INFO] Closing Chat.")

