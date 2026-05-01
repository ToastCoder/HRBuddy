from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import ollama
from core.logger import log
from core.config_loader import cfg

class HRBuddyEngine:
    def __init__(self, chunks):
        """
        Initialization parameters are pulled entirely from cfg (JSON).
        """
        log.info(f"[RAG] Initializing with model: {cfg['vector_store']['embedding_model']}")
        
        # 1. Embeddings - Configured via JSON
        self.embeddings = OllamaEmbeddings(
            model=cfg["vector_store"]["embedding_model"],
            base_url=cfg.get("ollama_base_url", "http://localhost:11434")
        )
        
        # 2. Vector DB - Search settings from JSON
        self.vectorstore = Chroma.from_documents(
            documents=chunks, 
            embedding=self.embeddings
        )
        
        # k (number of documents) is now a JSON parameter
        search_k = cfg["vector_store"].get("search_top_k", 2)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": search_k})
        
        log.info(f"[RAG] Search depth set to k={search_k}")

    def generate_response(self, user_input, history_text, session_id):
        # Retrieve context
        docs = self.retriever.invoke(user_input)
        context_block = "\n\n".join([doc.page_content for doc in docs])
        
        # 3. Prompting - Temperature and Model pulled from JSON
        log.info(f"[RAG] Generating response using {cfg['llm']['model']}...")
        
        ollama_client = ollama.Client(host=cfg.get("ollama_base_url", "http://localhost:11434"))
        
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

    def _build_prompt(self, user_input, history, session_id, context):
        # We can even move the system instructions to JSON if you want total control!
        return f"""You are a precise HR assistant speaking with {session_id}.
        
        CONTEXT:
        {context}
        
        HISTORY:
        {history}
        
        Question: {user_input}
        Answer:"""