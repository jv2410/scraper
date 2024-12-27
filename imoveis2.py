from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup
import time
from queue import Queue
import logging
import json
import os
from urllib.parse import urljoin, urlparse
import re
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Web Scraper API", description="API para extrair dados de páginas web.", version="1.0.0")

# CORS (Cross-Origin Resource Sharing) - importante para permitir requisições de outros domínios
origins = ["*"]  # Em produção, especifique os domínios permitidos, ex: ["http://meusite.com", "https://outro.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('scraper.log')])
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, start_url, target_endpoint):
        # ... (seu código da classe WebScraper permanece igual)

@app.get("/scrape/", summary="Executa o scraping de uma URL.", description="Este endpoint executa o scraping de uma URL fornecida e envia os dados para um webhook.")
async def scrape_endpoint(start_url: str = Query(..., description="URL inicial para o scraping")):
    """Executa o scraping."""
    try:
        if not start_url.startswith("http"):
            raise HTTPException(status_code=400, detail="A URL deve começar com http:// ou https://")

        scraper = WebScraper(start_url, "https://n8n.midvisiondigital.com.br/webhook/deda4a51-2907-41a8-8975-d6549f3c8b9c")
        scraper.scrape()
        scraper.compare_links()
        return {"message": f"Scraping concluído para {start_url}. Verifique o arquivo scraper.log para detalhes."}
    except requests.exceptions.RequestException as e:
        logger.exception(f"Erro de requisição durante o scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de requisição: {e}")
    except Exception as e:
        logger.exception(f"Erro interno durante o scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")

@app.get("/health", summary="Verifica a saúde da API", description="Este endpoint retorna um status 200 OK se a API estiver funcionando.")
async def health_check():
    """Verifica se a API está online."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
