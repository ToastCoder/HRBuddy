# HRBuddy
# core/ingestion.py

# Required Libraries
import os
from core.logger import log
from core.config_loader import cfg
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_pdf(file_path):
    """
    The main ingestion worker.
    Returns: List of Langchain Chunks
    """
    log.info(f"[Ingestion] Starting PDF processing: {file_path}")

    # 1. Text Extraction using your preferred Langchain Loader
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    # 2. Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg["ingestion"].get("chunk_size", 1000), 
        chunk_overlap=cfg["ingestion"].get("chunk_overlap", 150)
    )
    chunks = text_splitter.split_documents(pages)
    
    log.info(f"[Ingestion] Processing complete: {len(chunks)} text segments created.")
    return chunks