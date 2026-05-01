# HRBuddy
# core/rag_engine.py

# Required Libraries
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
import ollama
from core.logger import log
from core.config_loader import cfg

# Main Class
class HRBuddyEngine:
    def __init__(self, chunks):
        """
        Initialization parameters are pulled entirely from cfg (JSON).
        """
        log.info(f"[RAG] Initializing with model: {cfg['vector_store']['embedding_model']}")
        
        # Embeddings
        self.embeddings = OllamaEmbeddings(
            model=cfg["vector_store"]["embedding_model"],
            base_url=cfg.get("ollama_base_url", "http://localhost:11434")
        )
        
        # Vector DB
        self.vectorstore = Chroma.from_documents(
            documents=chunks, 
            embedding=self.embeddings
        )
        
        # k (number of documents)
        search_k = cfg["vector_store"].get("search_top_k", 2)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": search_k})
        
        log.info(f"[RAG] Search depth set to k={search_k}")

    # Generate Response
    def generate_response(self, user_input, history_text, session_id):
        '''
        Generating the response based on user input and history.
        '''

        # Retrieve context
        docs = self.retriever.invoke(user_input)
        context_block = "\n\n".join([doc.page_content for doc in docs])
        
        log.info(f"[RAG] Generating response using {cfg['llm']['model']}...")
        
        # Ollama Client
        ollama_client = ollama.Client(host=cfg.get("ollama_base_url", "http://localhost:11434"))
        
        # Generate Response
        response_stream = ollama_client.chat(
            model=cfg["llm"]["model"],
            messages=[{'role': 'user', 'content': self._build_prompt(user_input, history_text, session_id, context_block)}],
            stream=True,
            options={
                "temperature": cfg["llm"].get("temperature", 0.1),
                "num_ctx": cfg["llm"].get("context_window", 4096)
            }
        )
        return response_stream

    # Build Prompt
    def _build_prompt(self, user_input, history, session_id, context):
        '''
        Building the prompt for the LLM.
        '''
        
        return f"""You are a precise HR assistant speaking with {session_id}.
        
        CONTEXT:
        {context}
        
        HISTORY:
        {history}
        
        Question: {user_input}
        Answer:"""