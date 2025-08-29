#!/usr/bin/env python3

import logging
from typing import Dict, Any, List, Optional
from langchain_openai import OpenAI, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever
from vector_store import VectorStoreManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfinitePayRAGChain:
    
    def __init__(self, 
                 openai_api_key: str,
                 model_name: str = "gpt-4o-mini",
                 temperature: float = 0):

        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.temperature = temperature
        

        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        self.qa_chain: Optional[RetrievalQA] = None
        self.retriever: Optional[BaseRetriever] = None
        
    def create_portuguese_prompt(self) -> PromptTemplate:
        template = """
Você é um assistente de suporte da InfinitePay que responde perguntas com base EXCLUSIVAMENTE nos trechos de documentação fornecidos abaixo.

INSTRUÇÕES CRÍTICAS:
1. NUNCA invente, suponha ou adicione informações que não estejam EXPLICITAMENTE no contexto fornecido
2. Se o contexto contém informações específicas e relevantes para a pergunta, responda de forma direta e confiante
3. Se o contexto NÃO contém informações específicas sobre a pergunta, responda APENAS "Não sei."
4. NÃO adicione informações gerais, suposições ou conhecimento externo
5. NÃO mencione fontes na resposta - isso será adicionado automaticamente
6. Responda em português do Brasil, de forma clara e concisa
7. Seja profissional como um representante oficial da InfinitePay
8. Se as informações estão claramente disponíveis no contexto, não adicione expressões de incerteza

CONTEXTO:
{context}

PERGUNTA: {question}

RESPOSTA:
"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def setup_qa_chain(self, vector_store_manager: VectorStoreManager) -> None:

        self.retriever = vector_store_manager.get_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 10}
        )
        

        prompt = self.create_portuguese_prompt()
        

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        logger.info("QA chain setup completed")
    

    
    def format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        answer = result.get("result", "")
        source_docs = result.get("source_documents", [])
        

        sources = []
        seen_urls = set()
        
        for doc in source_docs:
            url = doc.metadata.get("source", "")
            title = doc.metadata.get("title", "Documento sem título")
            
            if url and url not in seen_urls:
                sources.append({
                    "url": url,
                    "title": title
                })
                seen_urls.add(url)
        

        sources = sources[:5]
        

        if sources:
            sources_text = "\n\n**Fontes:**\n"
            for i, source in enumerate(sources, 1):
                sources_text += f"{i}. [{source['title']}]({source['url']})\n"
        else:
            sources_text = ""
        

        formatted_answer = answer + sources_text
        
        return {
            "answer": formatted_answer,
            "raw_answer": answer,
            "sources": sources,
            "source_documents": source_docs
        }
    
    def ask(self, question: str) -> Dict[str, Any]:
        if not self.qa_chain:
            raise ValueError("QA chain not setup. Call setup_qa_chain() first.")
        
        logger.info(f"Processing question: {question}")
        
        try:

            result = self.qa_chain.invoke({"query": question})
            

            formatted_result = self.format_response(result)
            
            logger.info("Question processed successfully with RAG knowledge")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            
            return {
                "answer": "Não encontrei essa informação na Central de Ajuda. Sugiro entrar em contato pelos canais oficiais da InfinitePay.",
                "raw_answer": "",
                "sources": [],
                "source_documents": [],
                "error": str(e)
            }
    
    def batch_ask(self, questions: List[str]) -> List[Dict[str, Any]]:
        results = []
        
        for i, question in enumerate(questions):
            logger.info(f"Processing question {i+1}/{len(questions)}")
            result = self.ask(question)
            results.append({
                "question": question,
                **result
            })
        
        return results
    
    def get_relevant_documents(self, question: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.retriever:
            raise ValueError("Retriever not setup. Call setup_qa_chain() first.")
        
        docs = self.retriever.get_relevant_documents(question)
        
        formatted_docs = []
        for doc in docs[:k]:
            formatted_docs.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "title": doc.metadata.get("title", ""),
                "chunk_id": doc.metadata.get("chunk_id", 0),
                "token_count": doc.metadata.get("chunk_token_count", 0)
            })
        
        return formatted_docs


class RAGEvaluator:
    """Evaluate RAG system performance"""
    
    def __init__(self, rag_chain: InfinitePayRAGChain):
        self.rag_chain = rag_chain
    
    def evaluate_questions(self, test_questions: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluate the RAG system with test questions
        
        Args:
            test_questions: List of dicts with 'question' and optionally 'expected_sources'
        """
        results = []
        
        for test_case in test_questions:
            question = test_case["question"]
            expected_sources = test_case.get("expected_sources", [])
            
            # Get answer
            result = self.rag_chain.ask(question)
            
            # Check if expected sources are found
            found_sources = [s["url"] for s in result["sources"]]
            source_coverage = 0
            
            if expected_sources:
                matches = sum(1 for expected in expected_sources if any(expected in found for found in found_sources))
                source_coverage = matches / len(expected_sources)
            
            results.append({
                "question": question,
                "answer": result["answer"],
                "sources_found": len(result["sources"]),
                "source_coverage": source_coverage,
                "has_error": "error" in result
            })
        
        # Calculate overall metrics
        avg_sources = sum(r["sources_found"] for r in results) / len(results)
        avg_coverage = sum(r["source_coverage"] for r in results) / len(results)
        error_rate = sum(1 for r in results if r["has_error"]) / len(results)
        
        return {
            "results": results,
            "metrics": {
                "avg_sources_per_question": avg_sources,
                "avg_source_coverage": avg_coverage,
                "error_rate": error_rate,
                "total_questions": len(results)
            }
        }


def main():
    """Example usage of InfinitePayRAGChain"""
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
    
    # Setup vector store (assuming it exists)
    vector_manager = VectorStoreManager(
        openai_api_key=openai_api_key,
        store_type="faiss",
        persist_directory="./demo_vector_store"
    )
    
    # Try to load existing vector store
    if not vector_manager.load_vector_store():
        print("No vector store found. Please create one first using vector_store.py")
        return
    
    # Create RAG chain
    rag_chain = InfinitePayRAGChain(openai_api_key=openai_api_key)
    rag_chain.setup_qa_chain(vector_manager)
    
    # Test questions
    test_questions = [
        "Como encerrar minha conta InfinitePay?",
        "Quais são as taxas das maquininhas?",
        "Como entrar em contato com o suporte?",
        "Qual o prazo para receber o dinheiro?"
    ]
    
    print("\n=== Testando o Sistema RAG da InfinitePay ===")
    
    for question in test_questions:
        print(f"\n\nPergunta: {question}")
        print("-" * 50)
        
        result = rag_chain.ask(question)
        print(result["answer"])
        
        if "error" in result:
            print(f"\nErro: {result['error']}")


if __name__ == "__main__":
    main()