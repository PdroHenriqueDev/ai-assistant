#!/usr/bin/env python3
"""
Main Pipeline for InfinitePay RAG System

This script orchestrates the complete RAG pipeline: scraping, document processing,
vector store creation, and question answering.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Import our modules
from scraper import InfinitePayScraper
from document_processor import DocumentProcessor
from vector_store import VectorStoreManager
from rag_chain import InfinitePayRAGChain, RAGEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InfinitePayRAGPipeline:
    """Complete RAG pipeline for InfinitePay help center"""
    
    def __init__(self, 
                 openai_api_key: str,
                 base_url: str = "https://ajuda.infinitepay.io/pt-BR/",
                 articles_file: str = "infinitepay_articles.json",
                 vector_store_dir: str = "./infinitepay_vector_store",
                 store_type: str = "faiss"):
        """
        Initialize the RAG pipeline
        
        Args:
            openai_api_key: OpenAI API key
            base_url: Base URL for scraping
            articles_file: File to save/load scraped articles
            vector_store_dir: Directory for vector store persistence
            store_type: Type of vector store ('faiss' or 'chroma')
        """
        self.openai_api_key = openai_api_key
        self.base_url = base_url
        self.articles_file = articles_file
        self.vector_store_dir = vector_store_dir
        self.store_type = store_type
        
        # Initialize components
        self.scraper = InfinitePayScraper(base_url=base_url)
        self.processor = DocumentProcessor()
        self.vector_manager = VectorStoreManager(
            openai_api_key=openai_api_key,
            store_type=store_type,
            persist_directory=vector_store_dir
        )
        self.rag_chain = InfinitePayRAGChain(openai_api_key=openai_api_key)
        
        self.is_initialized = False
    
    def scrape_articles(self, max_articles: Optional[int] = None, force_rescrape: bool = False) -> List[Any]:
        """Scrape articles from InfinitePay help center"""
        articles_path = Path(self.articles_file)
        
        # Check if articles already exist
        if articles_path.exists() and not force_rescrape:
            logger.info(f"Loading existing articles from {self.articles_file}")
            articles = self.scraper.load_articles(self.articles_file)
            if articles:
                logger.info(f"Loaded {len(articles)} existing articles")
                return articles
        
        # Scrape new articles
        logger.info("Starting article scraping...")
        articles = self.scraper.scrape_all_articles(max_articles=max_articles)
        
        if articles:
            # Save articles
            self.scraper.save_articles(self.articles_file)
            logger.info(f"Scraped and saved {len(articles)} articles")
        else:
            logger.warning("No articles were scraped")
        
        return articles
    
    def process_documents(self, articles: List[Any]) -> List[Any]:
        """Process articles into LangChain documents"""
        logger.info("Processing articles into documents...")
        documents = self.processor.process_articles(articles)
        
        # Print processing statistics
        stats = self.processor.get_processing_stats(documents)
        logger.info("Document processing completed:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        return documents
    
    def create_vector_store(self, documents: List[Any], force_recreate: bool = False) -> bool:
        """Create or load vector store"""
        vector_store_path = Path(self.vector_store_dir)
        
        # Try to load existing vector store
        if vector_store_path.exists() and not force_recreate:
            logger.info("Attempting to load existing vector store...")
            if self.vector_manager.load_vector_store():
                logger.info("Successfully loaded existing vector store")
                return True
            else:
                logger.warning("Failed to load existing vector store, creating new one")
        
        # Create new vector store
        if not documents:
            logger.error("No documents available to create vector store")
            return False
        
        logger.info("Creating new vector store...")
        try:
            self.vector_manager.create_vector_store(documents)
            self.vector_manager.save_vector_store()
            logger.info("Vector store created and saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            return False
    
    def initialize_rag_chain(self) -> bool:
        """Initialize the RAG chain"""
        try:
            logger.info("Initializing RAG chain...")
            self.rag_chain.setup_qa_chain(self.vector_manager)
            self.is_initialized = True
            logger.info("RAG chain initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize RAG chain: {str(e)}")
            return False
    
    def setup_pipeline(self, 
                      max_articles: Optional[int] = None,
                      force_rescrape: bool = False,
                      force_recreate_vector_store: bool = False) -> bool:
        """Setup the complete pipeline"""
        logger.info("Setting up InfinitePay RAG pipeline...")
        
        # Step 1: Scrape articles
        articles = self.scrape_articles(max_articles, force_rescrape)
        if not articles:
            logger.error("No articles available")
            return False
        
        # Step 2: Process documents
        documents = self.process_documents(articles)
        if not documents:
            logger.error("No documents created")
            return False
        
        # Step 3: Create vector store
        if not self.create_vector_store(documents, force_recreate_vector_store):
            logger.error("Failed to create vector store")
            return False
        
        # Step 4: Initialize RAG chain
        if not self.initialize_rag_chain():
            logger.error("Failed to initialize RAG chain")
            return False
        
        logger.info("Pipeline setup completed successfully!")
        return True
    
    def ask(self, question: str) -> Dict[str, Any]:
        """Ask a question using the RAG system"""
        if not self.is_initialized:
            raise ValueError("Pipeline not initialized. Call setup_pipeline() first.")
        
        return self.rag_chain.ask(question)
    
    def interactive_mode(self):
        """Run interactive question-answering mode"""
        if not self.is_initialized:
            logger.error("Pipeline not initialized. Please run setup first.")
            return
        
        print("\n" + "="*60)
        print("🤖 InfinitePay RAG Assistant")
        print("Digite suas perguntas sobre a InfinitePay (ou 'quit' para sair)")
        print("="*60)
        
        while True:
            try:
                question = input("\n❓ Sua pergunta: ").strip()
                
                if question.lower() in ['quit', 'exit', 'sair', 'q']:
                    print("👋 Até logo!")
                    break
                
                if not question:
                    continue
                
                print("\n🔍 Buscando informações...")
                result = self.ask(question)
                
                print("\n" + "-"*50)
                print("📝 Resposta:")
                print(result["answer"])
                
                if "error" in result:
                    print(f"\n⚠️  Erro: {result['error']}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Até logo!")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {str(e)}")
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Run evaluation with test questions"""
        if not self.is_initialized:
            raise ValueError("Pipeline not initialized. Call setup_pipeline() first.")
        
        test_questions = [
            {"question": "Como encerrar minha conta InfinitePay?"},
            {"question": "Quais são as taxas das maquininhas?"},
            {"question": "Como entrar em contato com o suporte?"},
            {"question": "Qual o prazo para receber o dinheiro?"},
            {"question": "Como fazer um PIX?"},
            {"question": "Quais são os canais oficiais da InfinitePay?"},
            {"question": "Como solicitar uma maquininha?"},
            {"question": "Posso usar a maquininha sem internet?"}
        ]
        
        evaluator = RAGEvaluator(self.rag_chain)
        return evaluator.evaluate_questions(test_questions)
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the pipeline"""
        info = {
            "base_url": self.base_url,
            "articles_file": self.articles_file,
            "vector_store_dir": self.vector_store_dir,
            "store_type": self.store_type,
            "is_initialized": self.is_initialized
        }
        
        # Add vector store info if available
        try:
            vector_info = self.vector_manager.get_store_info()
            info["vector_store_info"] = vector_info
        except:
            info["vector_store_info"] = "Not available"
        
        return info


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="InfinitePay RAG Pipeline")
    parser.add_argument("--setup", action="store_true", help="Setup the pipeline")
    parser.add_argument("--interactive", action="store_true", help="Run interactive mode")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation")
    parser.add_argument("--question", type=str, help="Ask a single question")
    parser.add_argument("--max-articles", type=int, help="Maximum articles to scrape")
    parser.add_argument("--force-rescrape", action="store_true", help="Force re-scraping")
    parser.add_argument("--force-recreate-vector", action="store_true", help="Force vector store recreation")
    parser.add_argument("--store-type", choices=["faiss", "chroma"], default="faiss", help="Vector store type")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        logger.error("Please create a .env file with your OpenAI API key")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = InfinitePayRAGPipeline(
        openai_api_key=openai_api_key,
        store_type=args.store_type
    )
    
    # Setup pipeline if requested
    if args.setup:
        success = pipeline.setup_pipeline(
            max_articles=args.max_articles,
            force_rescrape=args.force_rescrape,
            force_recreate_vector_store=args.force_recreate_vector
        )
        if not success:
            logger.error("Pipeline setup failed")
            sys.exit(1)
    
    # Try to initialize if not already done
    if not pipeline.is_initialized:
        logger.info("Attempting to load existing pipeline...")
        if not pipeline.setup_pipeline():
            logger.error("Failed to initialize pipeline. Try running with --setup")
            sys.exit(1)
    
    # Handle different modes
    if args.question:
        result = pipeline.ask(args.question)
        print(f"\nPergunta: {args.question}")
        print("-" * 50)
        print(result["answer"])
    
    elif args.evaluate:
        print("\nExecutando avaliação do sistema...")
        eval_results = pipeline.run_evaluation()
        
        print("\n" + "="*60)
        print("📊 RESULTADOS DA AVALIAÇÃO")
        print("="*60)
        
        metrics = eval_results["metrics"]
        print(f"Total de perguntas: {metrics['total_questions']}")
        print(f"Média de fontes por pergunta: {metrics['avg_sources_per_question']:.2f}")
        print(f"Taxa de erro: {metrics['error_rate']:.2%}")
        
        print("\n📝 Detalhes por pergunta:")
        for result in eval_results["results"]:
            print(f"\n❓ {result['question']}")
            print(f"   Fontes encontradas: {result['sources_found']}")
            if result['has_error']:
                print("   ❌ Erro na resposta")
    
    elif args.interactive:
        pipeline.interactive_mode()
    
    else:
        # Show pipeline info
        info = pipeline.get_pipeline_info()
        print("\n" + "="*60)
        print("🔧 INFORMAÇÕES DO PIPELINE")
        print("="*60)
        for key, value in info.items():
            print(f"{key}: {value}")
        
        print("\n💡 Uso:")
        print("  --setup              : Configurar pipeline")
        print("  --interactive        : Modo interativo")
        print("  --question 'texto'   : Fazer uma pergunta")
        print("  --evaluate           : Executar avaliação")


if __name__ == "__main__":
    main()