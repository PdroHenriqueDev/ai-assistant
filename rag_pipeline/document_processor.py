#!/usr/bin/env python3

import logging
from typing import List, Dict, Any
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from scraper import Article


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    
    def __init__(self, 
                 chunk_size: int = 1200,
                 chunk_overlap: int = 150,
                 encoding_name: str = "cl100k_base"):

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        

        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name=encoding_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ": ", " ", ""]
        )
        
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def clean_text(self, text: str) -> str:

        text = ' '.join(text.split())
        

        text = text.replace('\xa0', ' ')
        text = text.replace('\u200b', '')
        

        text = ' '.join(text.split())
        
        return text.strip()
    
    def format_article_content(self, article: Article) -> str:
        content_parts = []
        

        if article.title:
            content_parts.append(f"# {article.title}")
        

        if article.content:
            content_parts.append(self.clean_text(article.content))
        
        return "\n\n".join(content_parts)
    
    def create_document_from_article(self, article: Article) -> Document:
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
        chunks = self.text_splitter.split_documents([document])
        

        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "chunk_token_count": self.count_tokens(chunk.page_content)
            })
        
        return chunks
    
    def process_articles(self, articles: List[Article]) -> List[Document]:
        all_documents = []
        
        logger.info(f"Processing {len(articles)} articles...")
        
        for i, article in enumerate(articles):
            try:

                document = self.create_document_from_article(article)
                

                token_count = self.count_tokens(document.page_content)
                
                if token_count <= self.chunk_size:
                    document.metadata["chunk_id"] = 0
                    document.metadata["total_chunks"] = 1
                    document.metadata["chunk_token_count"] = token_count
                    all_documents.append(document)
                else:
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
    from scraper import InfinitePayScraper
    

    scraper = InfinitePayScraper()
    articles = scraper.load_articles("infinitepay_articles.json")
    
    if not articles:
        print("No articles found. Please run the scraper first.")
        return
    

    processor = DocumentProcessor()
    documents = processor.process_articles(articles)
    

    stats = processor.get_processing_stats(documents)
    print("\nProcessing Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    

    if documents:
        print("\nSample Document:")
        doc = documents[0]
        print(f"Source: {doc.metadata['source']}")
        print(f"Title: {doc.metadata['title']}")
        print(f"Tokens: {doc.metadata['chunk_token_count']}")
        print(f"Content preview: {doc.page_content[:200]}...")


if __name__ == "__main__":
    main()