from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Web Scraper API", description="API para extrair dados de páginas web.", version="1.0.0")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('scraper.log')])
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, start_url, target_endpoint):
        self.start_url = start_url
        self.target_endpoint = target_endpoint
        self.visited_urls = set()

    def scrape(self):
        try:
            response = requests.get(self.start_url)
            response.raise_for_status()  # Lança uma exceção para códigos de status HTTP ruins (4xx ou 5xx)
            soup = BeautifulSoup(response.content, "html.parser")

            # Exemplo básico de extração (substitua com sua lógica real)
            links = []
            for link in soup.find_all("a"):
                href = link.get("href")
                absolute_url = urljoin(self.start_url, href)
                if absolute_url.startswith("http") and absolute_url not in self.visited_urls:
                    links.append(absolute_url)
                    self.visited_urls.add(absolute_url)
            logger.info(f"Encontrados {len(links)} links em {self.start_url}")

            # Envia os dados para o webhook (substitua com sua lógica real)
            # requests.post(self.target_endpoint, json={"links": links})
            logger.info(f"Dados enviados para {self.target_endpoint} (simulado).")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar {self.start_url}: {e}")
            raise

    def compare_links(self):
      logger.info("Comparação de links simulada.") #adicione sua lógica de comparação aqui

@app.get("/scrape/", summary="Executa o scraping de uma URL.")
async def scrape_endpoint(start_url: str = Query(..., description="URL inicial")):
    try:
        if not start_url.startswith("http"):
            raise HTTPException(status_code=400, detail="A URL deve começar com http:// ou https://")

        scraper = WebScraper(start_url, "https://n8n.midvisiondigital.com.br/webhook/deda4a51-2907-41a8-8975-d6549f3c8b9c")
        scraper.scrape()
        scraper.compare_links()
        return {"message": f"Scraping concluído para {start_url}."}
    except requests.exceptions.RequestException as e:
        logger.exception(f"Erro de requisição durante o scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de requisição: {e}")
    except Exception as e:
        logger.exception(f"Erro interno durante o scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")

@app.get("/health", summary="Verifica a saúde da API")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
