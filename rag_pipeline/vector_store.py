#!/usr/bin/env python3

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Chroma
from langchain_core.vectorstores import VectorStore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    
    def __init__(self, 
                 openai_api_key: str,
                 store_type: str = "faiss",
                 persist_directory: str = "./vector_store",
                 embedding_model: str = "text-embedding-3-large"):

        self.openai_api_key = openai_api_key
        self.store_type = store_type.lower()
        self.persist_directory = Path(persist_directory)
        self.embedding_model = embedding_model
        

        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model=embedding_model
        )
        
        self.vector_store: Optional[VectorStore] = None
        

        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
    def create_vector_store(self, documents: List[Document]) -> VectorStore:
        if not documents:
            raise ValueError("No documents provided to create vector store")
        
        logger.info(f"Creating {self.store_type} vector store with {len(documents)} documents...")
        
        if self.store_type == "faiss":
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
        elif self.store_type == "chroma":
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory)
            )
        else:
            raise ValueError(f"Unsupported store type: {self.store_type}")
        
        logger.info(f"Vector store created successfully with {len(documents)} documents")
        return self.vector_store
    
    def save_vector_store(self) -> None:
        if not self.vector_store:
            raise ValueError("No vector store to save")
        
        logger.info(f"Saving {self.store_type} vector store to {self.persist_directory}")
        
        if self.store_type == "faiss":

            faiss_path = self.persist_directory / "faiss_index"
            self.vector_store.save_local(str(faiss_path))
        elif self.store_type == "chroma":

            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
        
        logger.info("Vector store saved successfully")
    
    def load_vector_store(self) -> Optional[VectorStore]:
        logger.info(f"Loading {self.store_type} vector store from {self.persist_directory}")
        
        try:
            if self.store_type == "faiss":
                faiss_path = self.persist_directory / "faiss_index"
                if faiss_path.exists():
                    self.vector_store = FAISS.load_local(
                        str(faiss_path),
                        embeddings=self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                else:
                    logger.warning(f"FAISS index not found at {faiss_path}")
                    return None
            
            elif self.store_type == "chroma":
                if self.persist_directory.exists():
                    self.vector_store = Chroma(
                        persist_directory=str(self.persist_directory),
                        embedding_function=self.embeddings
                    )
                else:
                    logger.warning(f"Chroma directory not found at {self.persist_directory}")
                    return None
            
            logger.info("Vector store loaded successfully")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            return None
    
    def add_documents(self, documents: List[Document]) -> None:
        if not self.vector_store:
            raise ValueError("No vector store available. Create or load one first.")
        
        if not documents:
            logger.warning("No documents provided to add")
            return
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        if self.store_type == "faiss":

            new_store = FAISS.from_documents(documents, self.embeddings)
            self.vector_store.merge_from(new_store)
        elif self.store_type == "chroma":

            self.vector_store.add_documents(documents)
        
        logger.info("Documents added successfully")
    
    def get_retriever(self, 
                     search_type: str = "mmr",
                     search_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        if not self.vector_store:
            raise ValueError("No vector store available. Create or load one first.")
        
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def similarity_search(self, 
                         query: str, 
                         k: int = 5) -> List[Document]:
        if not self.vector_store:
            raise ValueError("No vector store available. Create or load one first.")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def get_store_info(self) -> Dict[str, Any]:
        if not self.vector_store:
            return {"status": "No vector store loaded"}
        
        info = {
            "store_type": self.store_type,
            "persist_directory": str(self.persist_directory),
            "embedding_model": self.embedding_model
        }
        

        try:
            if self.store_type == "faiss":
                info["document_count"] = self.vector_store.index.ntotal
            elif self.store_type == "chroma":

                info["document_count"] = "Available (count not directly accessible)"
        except Exception as e:
            info["document_count"] = f"Error getting count: {str(e)}"
        
        return info


def main():
    """Example usage of VectorStoreManager"""
    import os
    from dotenv import load_dotenv
    from document_processor import DocumentProcessor
    from scraper import InfinitePayScraper
    
    # Load environment variables
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    # Load and process articles
    scraper = InfinitePayScraper()
    articles = scraper.load_articles("infinitepay_articles.json")
    
    if not articles:
        print("No articles found. Please run the scraper first.")
        return
    
    processor = DocumentProcessor()
    documents = processor.process_articles(articles[:5])  # Use first 5 for demo
    
    # Create vector store
    vector_manager = VectorStoreManager(
        openai_api_key=openai_api_key,
        store_type="faiss",  # or "chroma"
        persist_directory="./demo_vector_store"
    )
    
    # Create and save vector store
    vector_store = vector_manager.create_vector_store(documents)
    vector_manager.save_vector_store()
    
    # Test retrieval
    query = "Como encerrar minha conta?"
    results = vector_manager.similarity_search(query, k=3)
    
    print(f"\nQuery: {query}")
    print(f"Found {len(results)} relevant documents:")
    
    for i, doc in enumerate(results):
        print(f"\n{i+1}. {doc.metadata['title']}")
        print(f"   Source: {doc.metadata['source']}")
        print(f"   Content: {doc.page_content[:200]}...")
    
    # Print store info
    info = vector_manager.get_store_info()
    print("\nVector Store Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()