import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Add the rag_pipeline directory to Python path
rag_pipeline_path = Path(__file__).parent.parent / "rag_pipeline"
sys.path.insert(0, str(rag_pipeline_path))

try:
    from main_pipeline import InfinitePayRAGPipeline
except ImportError:
    # Fallback import path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rag_pipeline.main_pipeline import InfinitePayRAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="InfinitePay RAG API",
    description="API for InfinitePay Support RAG System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    max_sources: int = 5

class SourceInfo(BaseModel):
    url: str
    title: str

class QuestionResponse(BaseModel):
    answer: str
    raw_answer: str
    sources: List[SourceInfo]
    processing_time: float
    error: str | None = None

class PipelineStatus(BaseModel):
    is_initialized: bool
    total_documents: int
    vector_store_type: str
    last_updated: str = None

class SetupRequest(BaseModel):
    max_articles: int = 100
    force_rescrape: bool = False
    force_recreate_vector: bool = False

rag_pipeline = None

@app.on_event("startup")
async def startup_event():
    global rag_pipeline
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return
        
        rag_pipeline = InfinitePayRAGPipeline(
            openai_api_key=openai_api_key,
            base_url="https://ajuda.infinitepay.io/pt-BR/",
            articles_file=str(rag_pipeline_path / "infinitepay_articles.json"),
            vector_store_dir=str(rag_pipeline_path / "infinitepay_vector_store"),
            store_type="faiss"
        )
        
        if Path(rag_pipeline_path / "infinitepay_articles.json").exists():
            logger.info("Loading existing RAG pipeline...")
            articles = rag_pipeline.scraper.load_articles(
                str(rag_pipeline_path / "infinitepay_articles.json")
            )
            if articles:
                documents = rag_pipeline.process_documents(articles)
                if rag_pipeline.vector_manager.load_vector_store():
                    rag_pipeline.initialize_rag_chain()
                    logger.info("RAG pipeline loaded successfully")
                else:
                    logger.warning("Failed to load vector store")
        
        logger.info("RAG API startup completed")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "InfinitePay RAG API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    global rag_pipeline
    
    return {
        "status": "healthy",
        "pipeline_initialized": rag_pipeline is not None and rag_pipeline.is_initialized
    }

@app.get("/status", response_model=PipelineStatus)
async def get_pipeline_status():
    global rag_pipeline
    
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        info = rag_pipeline.get_pipeline_info()
        vector_info = info.get("vector_store_info", {})
        
        return PipelineStatus(
            is_initialized=rag_pipeline.is_initialized,
            total_documents=vector_info.get("document_count", 0),
            vector_store_type=info.get("store_type", "unknown")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

@app.post("/setup")
async def setup_pipeline(request: SetupRequest):
    global rag_pipeline
    
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not available")
    
    try:
        logger.info(f"Setting up pipeline with {request.max_articles} articles")
        
        success = rag_pipeline.setup_pipeline(
            max_articles=request.max_articles,
            force_rescrape=request.force_rescrape,
            force_recreate_vector_store=request.force_recreate_vector
        )
        
        if success:
            return {
                "status": "success",
                "message": "Pipeline setup completed successfully",
                "is_initialized": rag_pipeline.is_initialized
            }
        else:
            raise HTTPException(status_code=500, detail="Pipeline setup failed")
            
    except Exception as e:
        logger.error(f"Error setting up pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Setup error: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    global rag_pipeline
    
    if not rag_pipeline or not rag_pipeline.is_initialized:
        raise HTTPException(
            status_code=503, 
            detail="Pipeline not initialized. Please setup the pipeline first."
        )
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Processing question: {request.question}")
        result = rag_pipeline.ask(request.question)
        
        processing_time = time.time() - start_time
        
        sources = [
            SourceInfo(url=source["url"], title=source["title"])
            for source in result.get("sources", [])[:request.max_sources]
        ]
        
        return QuestionResponse(
            answer=result.get("answer", ""),
            raw_answer=result.get("raw_answer", ""),
            sources=sources,
            processing_time=processing_time,
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/documents/{query}")
async def get_relevant_documents(query: str, k: int = 5):
    global rag_pipeline
    
    if not rag_pipeline or not rag_pipeline.is_initialized:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        documents = rag_pipeline.rag_chain.get_relevant_documents(query, k=k)
        return {
            "query": query,
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/evaluate")
async def run_evaluation():
    """Run system evaluation"""
    global rag_pipeline
    
    if not rag_pipeline or not rag_pipeline.is_initialized:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        results = rag_pipeline.run_evaluation()
        return results
    except Exception as e:
        logger.error(f"Error running evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)