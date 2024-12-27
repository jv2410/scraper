import requests
from bs4 import BeautifulSoup
import time
from queue import Queue
import logging
import json
import os
from urllib.parse import urljoin, urlparse
import re

class WebScraper:
    def __init__(self, start_url, target_endpoint):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.target_endpoint = target_endpoint
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('scraper.log')])
        self.logger = logging.getLogger(__name__)

        self.processed_file = 'processed_links.json'
        self.processed_links = self._load_processed_links()
        self.visited_urls = set()
        self.queue = Queue()
        self.queue.put(self.start_url)

    def _load_processed_links(self):
        try:
            if os.path.exists(self.processed_file):
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            return set()
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _save_processed_link(self, link):
        self.processed_links.add(link)
        try:
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.processed_links), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar links processados: {e}")

    def _extract_links(self, html): #extrai os links q seguem o padrao /imovel/numeros/
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for link in soup.find_all('a', href=True):
            url = urljoin(self.start_url, link['href'])
            if re.search(r"^" + re.escape(self.start_url) + r"/imovel/\d+/", url) and url not in self.visited_urls and url not in self.processed_links:
                links.append(url)
        return list(set(links))
    
    def _extract_all_links(self, html): #extrai todos os links da pagina
        soup = BeautifulSoup(html, 'html.parser')
        all_links = set()
        for link in soup.find_all('a', href=True):
            url = urljoin(self.start_url, link['href'])
            if url.startswith(self.start_url):
                all_links.add(url)
        return list(all_links)

    def _extract_data(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        data = {"source_link": url}
        try:
            text_content = soup.get_text(separator='\n', strip=True)
            data['content'] = text_content
        except Exception as e:
            self.logger.error(f"Erro ao extrair conteúdo: {e}")
            data['content'] = "Erro ao extrair conteúdo"
        return data

    def compare_links(self):
        try:
            with open("all_links.json", 'r', encoding='utf-8') as f:
                all_links = set(json.load(f))
        except FileNotFoundError:
            self.logger.error("all_links.json não encontrado. Execute o scraping primeiro.")
            return

        missing_links = []
        for link in all_links:
            if re.search(r"^" + re.escape(self.start_url) + r"/imovel/\d+/", link) and link not in self.processed_links:
                missing_links.append(link)

        if missing_links:
            with open("missing_links.json", "w", encoding='utf-8') as outfile:
                json.dump(missing_links, outfile, ensure_ascii=False, indent=4)
            self.logger.info(f"Links faltantes salvos em missing_links.json: {len(missing_links)} links.")
        else:
            self.logger.info("Todos os links com código numérico foram processados.")

    def scrape(self):
        all_extracted_links = set()
        while not self.queue.empty():
            url = self.queue.get()
            if url not in self.visited_urls:
                self.logger.info(f"Acessando: {url}")
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    self.visited_urls.add(url)
                    self._save_processed_link(url)

                    extracted_data = self._extract_data(response.text, url)
                    print(f"Dados extraídos: {extracted_data}")

                    try:
                        webhook_response = requests.post(self.target_endpoint, json=extracted_data, timeout=10)
                        webhook_response.raise_for_status()
                        self.logger.info(f"Dados enviados para o webhook. Resposta: {webhook_response.text}")
                    except requests.exceptions.RequestException as e:
                        self.logger.error(f"Erro ao enviar dados para o webhook: {e}")

                    new_links = self._extract_links(response.text)
                    for link in new_links:
                        self.queue.put(link)
                    time.sleep(1)

                    novos_links = self._extract_all_links(response.text)
                    for link in novos_links:
                        all_extracted_links.add(link)
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Erro ao acessar {url}: {e}")
                except Exception as e:
                    self.logger.error(f"Erro genérico durante o scraping de {url}: {e}")

        with open("all_links.json", "w", encoding='utf-8') as outfile:
            json.dump(list(all_extracted_links), outfile, ensure_ascii=False, indent=4)
        self.logger.info(f"Todos os links extraídos salvos em all_links.json: {len(all_extracted_links)} links.")


if __name__ == "__main__":
    START_URL = "https://maisfacilimobiliaria.com.br"
    TARGET_ENDPOINT = "https://n8n.midvisiondigital.com.br/webhook/deda4a51-2907-41a8-8975-d6549f3c8b9c"

    scraper = WebScraper(START_URL, TARGET_ENDPOINT)

    print("\nDeseja continuar com o scraping completo? (s/n)")
    response = input().lower()
    if response == 's':
        print("Iniciando o scraping...")
        scraper.scrape()
        scraper.compare_links()
    else:
        print("Scraping cancelado.")