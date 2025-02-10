#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
docs-to-markdown.py

Implementación de un crawler BFS multi-URL con Crawl4AI para extraer documentación.
- Sigue enlaces internos del mismo dominio, evita bucles (visited)
- Opción de filtrar contenido irrelevante con LLM (LLMContentFilter) o heurístico (PruningContentFilter)
- Replica la estructura de directorios del sitio en la carpeta de salida .md

Modo de uso (ejemplos):
  python docs-to-markdown.py https://example.com/docs --llm --doc_name example_docs
  python docs-to-markdown.py https://example.com/docs --doc_name example_docs

Requisitos:
  pip install "crawl4ai[all]" python-dotenv
  # y si usas GPT/OpenAI => configurar OPENAI_API_KEY en .env
"""

import os
import sys
import asyncio
import time
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

# Cargar variables de entorno
load_dotenv()

# Configurar consola rica
console = Console()

# Import principal de Crawl4AI
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
# Dispatcher para manejar concurrency
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

# Filtros (LLM vs heurístico)
try:
    from crawl4ai.content_filter_strategy import LLMContentFilter, PruningContentFilter
except ImportError:
    console.print("[red]Error:[/] Necesitas instalar crawl4ai[all] para usar content_filter_strategy.")
    sys.exit(1)

class CrawlStats:
    def __init__(self):
        self.total_urls = 0
        self.processed_urls = 0
        self.success_urls = 0
        self.failed_urls = 0
        self.start_time = time.time()
    
    def add_url(self):
        self.total_urls += 1
    
    def url_processed(self, success: bool):
        self.processed_urls += 1
        if success:
            self.success_urls += 1
        else:
            self.failed_urls += 1
    
    def get_elapsed_time(self):
        return time.time() - self.start_time
    
    def display(self):
        table = Table(title="Crawling Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total URLs", str(self.total_urls))
        table.add_row("Processed URLs", str(self.processed_urls))
        table.add_row("Successful", str(self.success_urls))
        table.add_row("Failed", str(self.failed_urls))
        table.add_row("Elapsed Time", f"{self.get_elapsed_time():.2f}s")
        
        console.print(table)

def is_same_domain(base_domain: str, link: str) -> bool:
    """
    Verifica si 'link' pertenece al mismo dominio (o subdominio) que base_domain.
    """
    parsed = urlparse(link)
    if not parsed.netloc:
        return False
    return (parsed.netloc == base_domain) or parsed.netloc.endswith(f".{base_domain}")

def build_local_filepath(output_dir: str, doc_name: str, url: str) -> str:
    """
    Genera la ruta local replicando la estructura de subcarpetas
    según el path de la URL. E.g.:
      URL: https://example.com/docs/intro/getting-started.html
      => docs_outputs/example_docs/docs/intro/getting-started.html.md
    """
    parsed = urlparse(url)
    # path sin el primer '/'
    subpath = parsed.path.lstrip("/")
    if not subpath:
        subpath = "index.html"  # caso URL base => index

    dirname = os.path.dirname(subpath)      # e.g. "docs/intro"
    filename = os.path.basename(subpath)    # e.g. "getting-started.html"
    if not filename:
        filename = "index.html"             # si path terminaba en '/'

    local_dir = os.path.join(output_dir, doc_name, dirname)
    os.makedirs(local_dir, exist_ok=True)

    final_name = filename + ".md"
    return os.path.join(local_dir, final_name)

async def crawl_all_docs(
    start_url: str,
    doc_name: str,
    use_llm: bool = False
) -> None:
    """
    BFS: rastrea la doc y extrae Markdown, respetando estructura de carpetas.
    - start_url: URL principal
    - doc_name: nombre de la carpeta para esta documentación
    - use_llm: True => LLMContentFilter, False => PruningContentFilter
    """
    # Obtener configuración desde .env
    max_depth = int(os.getenv("MAX_DEPTH", 2))
    output_dir = os.getenv("OUTPUT_DIR", "docs_outputs")

    # Mostrar configuración inicial
    console.print(Panel.fit(
        f"[bold green]Starting crawler[/]\n"
        f"URL: [cyan]{start_url}[/]\n"
        f"Depth: [cyan]{max_depth}[/]\n"
        f"Output: [cyan]{output_dir}/{doc_name}[/]\n"
        f"Filter: [cyan]{'LLM' if use_llm else 'Heuristic'}[/]"
    ))

    parsed = urlparse(start_url)
    base_domain = parsed.netloc

    visited = set()
    to_crawl = [(start_url, 0)]
    
    # Inicializar estadísticas
    stats = CrawlStats()
    stats.add_url()  # URL inicial

    browser_cfg = BrowserConfig(headless=True, verbose=False)
    console.print("[bold blue]Initializing browser...[/]")

    # Definir content filter
    if use_llm:
        instruction = (
            "Extrae el contenido esencial de la documentación en formato Markdown, "
            "omitiendo menús, sidebars, footers y cualquier sección irrelevante."
        )
        content_filter = LLMContentFilter(
            provider="openai/gpt-4",
            api_token=os.getenv("OPENAI_API_KEY", ""),
            instruction=instruction,
            chunk_token_threshold=1500,
            overlap_rate=0.0,
            verbose=True
        )
    else:
        content_filter = PruningContentFilter(
            threshold=0.5,
            min_word_threshold=30
        )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        content_filter=content_filter
    )

    # Podríamos cambiar a SemaphoreDispatcher si queremos un límite fijo
    dispatcher = MemoryAdaptiveDispatcher(
        max_session_permit=5
    )

    os.makedirs(os.path.join(output_dir, doc_name), exist_ok=True)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task_crawl = progress.add_task("[cyan]Crawling...", total=None)
            
            while to_crawl:
                # Tomamos un batch de 5
                batch = []
                while to_crawl and len(batch) < 5:
                    url, depth = to_crawl.pop(0)
                    if url in visited:
                        continue
                    visited.add(url)
                    batch.append((url, depth))

                if not batch:
                    break

                batch_urls = [b[0] for b in batch]
                progress.update(task_crawl, description=f"[cyan]Processing {len(batch)} URLs...")

                results = await crawler.arun_many(
                    urls=batch_urls,
                    config=run_cfg,
                    dispatcher=dispatcher
                )
                for result in results:
                    if result.success:
                        console.print(f"[green]✓[/] {result.url}")
                        stats.url_processed(True)
                        
                        # Identificar la profundidad
                        idx = batch_urls.index(result.url)
                        current_depth = batch[idx][1]

                        # Markdown final (fit_markdown o raw)
                        if use_llm:
                            md = result.markdown_v2.fit_markdown or result.markdown
                        else:
                            md = result.markdown or ""

                        # Generar ruta local replicando path
                        local_md_file = build_local_filepath(output_dir, doc_name, result.url)
                        with open(local_md_file, "w", encoding="utf-8") as f:
                            f.write(md)

                        if current_depth < max_depth:
                            # Explorar más links internos
                            in_links = result.links.get("internal", [])
                            next_depth = current_depth + 1
                            for link_obj in in_links:
                                href = link_obj["href"]
                                abs_url = urljoin(result.url, href)
                                if is_same_domain(base_domain, abs_url) and abs_url not in visited:
                                    to_crawl.append((abs_url, next_depth))
                                    stats.add_url()
                    else:
                        console.print(f"[red]✗[/] {result.url} => {result.error_message}")
                        stats.url_processed(False)

    # Mostrar estadísticas finales
    console.print("\n[bold green]Crawling completed![/]")
    stats.display()

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Crawler BFS multi-url con subdirectorios")
    parser.add_argument("start_url", help="URL inicial (documentación)")
    parser.add_argument("--doc_name", required=True, help="Nombre de la carpeta para esta documentación")
    parser.add_argument("--llm", action="store_true", help="Activar filtrado con LLMContentFilter")
    return parser.parse_args()

async def main_cli():
    args = parse_args()
    await crawl_all_docs(
        start_url=args.start_url,
        doc_name=args.doc_name,
        use_llm=args.llm
    )

if __name__ == "__main__":
    asyncio.run(main_cli())
