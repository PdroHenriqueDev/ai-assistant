# InfinitePay RAG System

Um sistema completo de **Retrieval-Augmented Generation (RAG)** para a Central de Ajuda da InfinitePay, construído com LangChain e Python.

## 📋 Visão Geral

Este sistema implementa um pipeline RAG que:
- 🕷️ **Coleta** todos os artigos da Central de Ajuda da InfinitePay
- 📄 **Processa** o conteúdo em documentos estruturados
- 🔍 **Indexa** usando embeddings OpenAI e FAISS/Chroma
- 🤖 **Responde** perguntas em português com base no conhecimento coletado
- 📚 **Inclui fontes** (URLs) nas respostas

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Scraper   │───▶│ Document Processor│───▶│  Vector Store   │
│   (scraper.py)  │    │(document_processor)│    │(vector_store.py)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Main Pipeline  │◀───│   RAG Chain      │◀───│   Retriever     │
│(main_pipeline.py)│    │  (rag_chain.py)  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📦 Componentes

### 1. **Web Scraper** (`scraper.py`)
- Coleta artigos da Central de Ajuda da InfinitePay
- Rate limiting respeitoso (0.5s entre requests)
- Deduplicação de URLs
- Extração de texto limpo (títulos, parágrafos, listas)
- Persistência em JSON

### 2. **Document Processor** (`document_processor.py`)
- Converte artigos em documentos LangChain
- Chunking inteligente (~1200 tokens, overlap de 150)
- Limpeza e normalização de texto
- Metadados estruturados (fonte, título)

### 3. **Vector Store** (`vector_store.py`)
- Suporte para FAISS e Chroma
- Embeddings OpenAI
- Persistência em disco
- Busca por similaridade e MMR

### 4. **RAG Chain** (`rag_chain.py`)
- Chain RetrievalQA com GPT-4o-mini
- Prompt em português brasileiro
- Formatação de respostas com fontes
- Sistema de avaliação integrado

### 5. **Main Pipeline** (`main_pipeline.py`)
- Orquestração completa do pipeline
- Interface CLI e modo interativo
- Configuração automática
- Logging detalhado

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- Chave da API OpenAI

### 1. Clone e Configure o Ambiente

```bash
# Clone o repositório
git clone <repository-url>
cd rag_pipeline

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Dependências Necessárias

Crie um arquivo `requirements.txt`:

```txt
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
openai>=1.0.0
faiss-cpu>=1.7.4
chromadb>=0.4.0
beautifulsoup4>=4.12.0
requests>=2.31.0
python-dotenv>=1.0.0
tiktoken>=0.5.0
numpy>=1.24.0
```

## 📖 Uso

### Configuração Inicial

```bash
# Configure o pipeline completo
python main_pipeline.py --setup

# Configure com limite de artigos (para testes)
python main_pipeline.py --setup --max-articles 50

# Force re-scraping
python main_pipeline.py --setup --force-rescrape
```

### Modo Interativo

```bash
# Inicie o modo interativo
python main_pipeline.py --interactive
```

### Pergunta Única

```bash
# Faça uma pergunta específica
python main_pipeline.py --question "Como encerrar minha conta InfinitePay?"
```

### Avaliação do Sistema

```bash
# Execute avaliação automática
python main_pipeline.py --evaluate
```

### Exemplos Programáticos

```python
from main_pipeline import InfinitePayRAGPipeline

# Inicialize o pipeline
pipeline = InfinitePayRAGPipeline(openai_api_key="your-key")

# Configure (uma vez)
pipeline.setup_pipeline()

# Faça perguntas
result = pipeline.ask("Como solicitar uma maquininha?")
print(result["answer"])
```

## 🔧 Configuração Avançada

### Tipos de Vector Store

```python
# FAISS (padrão, mais rápido)
pipeline = InfinitePayRAGPipeline(
    openai_api_key="your-key",
    store_type="faiss"
)

# Chroma (mais recursos)
pipeline = InfinitePayRAGPipeline(
    openai_api_key="your-key",
    store_type="chroma"
)
```

### Parâmetros de Chunking

```python
from document_processor import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=1500,      # Tamanho do chunk
    chunk_overlap=200,    # Overlap entre chunks
    model_name="gpt-4"    # Modelo para contagem de tokens
)
```

### Configuração do Retriever

```python
from rag_chain import InfinitePayRAGChain

rag = InfinitePayRAGChain(
    openai_api_key="your-key",
    model_name="gpt-4o-mini",
    temperature=0,
    retriever_k=5,        # Número de documentos recuperados
    search_type="mmr"     # ou "similarity"
)
```

## 📊 Exemplos de Uso

### Exemplo Básico

```python
# Execute o exemplo básico
python example_usage.py
```

### Perguntas de Exemplo

| Categoria | Pergunta | Resposta Esperada |
|-----------|----------|-------------------|
| **Conta** | "Como encerrar minha conta?" | Instruções + URL do artigo |
| **Maquininha** | "Quais são as taxas?" | Lista de taxas + fontes |
| **PIX** | "Como fazer um PIX?" | Passo a passo + URLs |
| **Suporte** | "Canais oficiais?" | Lista de contatos + fontes |

### Formato de Resposta

```json
{
  "answer": "Para encerrar sua conta InfinitePay, você deve...\n\nFontes:\n- https://ajuda.infinitepay.io/pt-BR/articles/...",
  "sources": [
    "https://ajuda.infinitepay.io/pt-BR/articles/123",
    "https://ajuda.infinitepay.io/pt-BR/articles/456"
  ],
  "response_time": 2.34
}
```

## 🧪 Testes e Avaliação

### Métricas Automáticas

```python
# Execute avaliação completa
eval_results = pipeline.run_evaluation()

print(f"Taxa de sucesso: {1 - eval_results['metrics']['error_rate']:.2%}")
print(f"Fontes por pergunta: {eval_results['metrics']['avg_sources_per_question']:.1f}")
print(f"Tempo médio: {eval_results['metrics']['avg_response_time']:.2f}s")
```

### Testes Personalizados

```python
from rag_chain import RAGEvaluator

evaluator = RAGEvaluator(pipeline.rag_chain)

custom_questions = [
    {"question": "Sua pergunta aqui", "expected_sources": ["url1", "url2"]}
]

results = evaluator.evaluate_questions(custom_questions)
```

## 🔍 Monitoramento e Logs

### Configuração de Logging

```python
import logging

# Configure logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_pipeline.log'),
        logging.StreamHandler()
    ]
)
```

### Métricas de Performance

```python
# Obtenha informações do pipeline
info = pipeline.get_pipeline_info()
print(f"Documentos indexados: {info['vector_store_info']['document_count']}")
print(f"Última atualização: {info['vector_store_info']['last_updated']}")
```

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main_pipeline.py", "--interactive"]
```

### FastAPI (Opcional)

```python
from fastapi import FastAPI
from main_pipeline import InfinitePayRAGPipeline

app = FastAPI()
pipeline = InfinitePayRAGPipeline(openai_api_key="your-key")
pipeline.setup_pipeline()

@app.post("/ask")
async def ask_question(question: str):
    return pipeline.ask(question)
```

## 🔧 Troubleshooting

### Problemas Comuns

1. **Erro de API Key**
   ```
   ❌ OPENAI_API_KEY não encontrada
   ✅ Verifique o arquivo .env
   ```

2. **Falha no Scraping**
   ```
   ❌ Timeout ou erro de conexão
   ✅ Verifique conectividade e rate limiting
   ```

3. **Vector Store Corrompido**
   ```bash
   # Force recriação
   python main_pipeline.py --setup --force-recreate-vector
   ```

4. **Memória Insuficiente**
   ```python
   # Reduza o número de artigos
   pipeline.setup_pipeline(max_articles=100)
   ```

### Debug Mode

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Ou via CLI
python main_pipeline.py --setup --verbose
```

## 📈 Otimizações

### Performance
- Use FAISS para datasets grandes (>10k documentos)
- Configure `chunk_size` baseado no seu modelo LLM
- Implemente cache para perguntas frequentes

### Qualidade
- Ajuste `retriever_k` baseado na complexidade das perguntas
- Use re-ranking para melhor precisão
- Implemente feedback loop para melhorias contínuas

### Custos
- Use `gpt-4o-mini` para reduzir custos
- Implemente cache de embeddings
- Otimize chunk size para reduzir tokens

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte

Para dúvidas ou problemas:
1. Verifique a seção de Troubleshooting
2. Execute os exemplos de uso
3. Abra uma issue no repositório

---

**Desenvolvido com ❤️ para a comunidade InfinitePay**