#!/usr/bin/env python3
"""
Document Processor for InfinitePay RAG Pipeline

This module processes scraped articles and converts them into LangChain Documents
with proper text chunking and metadata for the RAG system.
"""

import logging
from typing import List, Dict, Any
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from scraper import Article

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes articles into LangChain Documents with chunking"""
    
    def __init__(self, 
                 chunk_size: int = 1200,
                 chunk_overlap: int = 150,
                 encoding_name: str = "cl100k_base"):
        """
        Initialize document processor
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Token overlap between chunks
            encoding_name: Tokenizer encoding to use
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        
        # Initialize text splitter with token-based splitting
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name=encoding_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ": ", " ", ""]
        )
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the specified encoding"""
        return len(self.encoding.encode(text))
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.replace('\xa0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')  # Zero-width space
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text.strip()
    
    def format_article_content(self, article: Article) -> str:
        """Format article content for processing"""
        content_parts = []
        
        # Add title
        if article.title:
            content_parts.append(f"# {article.title}")
        
        # Add content
        if article.content:
            content_parts.append(self.clean_text(article.content))
        
        return "\n\n".join(content_parts)
    
    def create_document_from_article(self, article: Article) -> Document:
        """Create a LangChain Document from an Article"""
        content = self.format_article_content(article)
        
        metadata = {
            "source": article.url,
            "title": article.title or "Untitled",
            "token_count": self.count_tokens(content)
        }
        
        return Document(
            page_content=content,
            metadata=metadata
        )
    
    def chunk_document(self, document: Document) -> List[Document]:
        """Split a document into chunks"""
        chunks = self.text_splitter.split_documents([document])
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "chunk_token_count": self.count_tokens(chunk.page_content)
            })
        
        return chunks
    
    def process_articles(self, articles: List[Article]) -> List[Document]:
        """Process a list of articles into chunked documents"""
        all_documents = []
        
        logger.info(f"Processing {len(articles)} articles...")
        
        for i, article in enumerate(articles):
            try:
                # Create document from article
                document = self.create_document_from_article(article)
                
                # Check if document needs chunking
                token_count = self.count_tokens(document.page_content)
                
                if token_count <= self.chunk_size:
                    # Small document, no chunking needed
                    document.metadata["chunk_id"] = 0
                    document.metadata["total_chunks"] = 1
                    document.metadata["chunk_token_count"] = token_count
                    all_documents.append(document)
                else:
                    # Large document, needs chunking
                    chunks = self.chunk_document(document)
                    all_documents.extend(chunks)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(articles)} articles")
                    
            except Exception as e:
                logger.error(f"Error processing article {article.url}: {str(e)}")
                continue
        
        logger.info(f"Created {len(all_documents)} document chunks from {len(articles)} articles")
        return all_documents
    
    def get_processing_stats(self, documents: List[Document]) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        if not documents:
            return {}
        
        token_counts = [doc.metadata.get("chunk_token_count", 0) for doc in documents]
        unique_sources = set(doc.metadata.get("source", "") for doc in documents)
        
        return {
            "total_documents": len(documents),
            "unique_sources": len(unique_sources),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_chunk": sum(token_counts) / len(token_counts) if token_counts else 0,
            "min_tokens": min(token_counts) if token_counts else 0,
            "max_tokens": max(token_counts) if token_counts else 0
         }


def main():
    """Example usage of DocumentProcessor"""
    from scraper import InfinitePayScraper
    
    # Load scraped articles
    scraper = InfinitePayScraper()
    articles = scraper.load_articles("infinitepay_articles.json")
    
    if not articles:
        print("No articles found. Please run the scraper first.")
        return
    
    # Process articles
    processor = DocumentProcessor()
    documents = processor.process_articles(articles)
    
    # Print statistics
    stats = processor.get_processing_stats(documents)
    print("\nProcessing Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show sample document
    if documents:
        print("\nSample Document:")
        doc = documents[0]
        print(f"Source: {doc.metadata['source']}")
        print(f"Title: {doc.metadata['title']}")
        print(f"Tokens: {doc.metadata['chunk_token_count']}")
        print(f"Content preview: {doc.page_content[:200]}...")


if __name__ == "__main__":
    main()