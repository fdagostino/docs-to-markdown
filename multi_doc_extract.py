#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
multi_doc_extract.py

Implementación de un crawler BFS multi-URL con Crawl4AI para extraer documentación.
- Sigue enlaces internos del mismo dominio, evita bucles (visited)
- Opción de filtrar contenido irrelevante con LLM (LLMContentFilter) o heurístico (PruningContentFilter)
- Replica la estructura de directorios del sitio en la carpeta de salida .md

Modo de uso (ejemplos):
  python multi_doc_extract.py https://example.com/docs --depth 3 --llm --out docs_outputs
  python multi_doc_extract.py https://example.com/docs --depth 2 --out docs_outputs

Requisitos:
  pip install "crawl4ai[all]" python-dotenv
  # y si usas GPT/OpenAI => configurar OPENAI_API_KEY en .env
"""

import os
import sys
import asyncio
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Import principal de Crawl4AI
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
# Dispatcher para manejar concurrency
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

# Filtros (LLM vs heurístico)
try:
    from crawl4ai.content_filter_strategy import LLMContentFilter, PruningContentFilter
except ImportError:
    print("Necesitas instalar crawl4ai[all] para usar content_filter_strategy.")
    sys.exit(1)

def is_same_domain(base_domain: str, link: str) -> bool:
    """
    Verifica si 'link' pertenece al mismo dominio (o subdominio) que base_domain.
    """
    parsed = urlparse(link)
    if not parsed.netloc:
        return False
    return (parsed.netloc == base_domain) or parsed.netloc.endswith(f".{base_domain}")

def build_local_filepath(output_dir: str, url: str) -> str:
    """
    Genera la ruta local replicando la estructura de subcarpetas
    según el path de la URL. E.g.:
      URL: https://example.com/docs/intro/getting-started.html
      => docs_outputs/docs/intro/getting-started.html.md
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

    local_dir = os.path.join(output_dir, dirname)
    os.makedirs(local_dir, exist_ok=True)

    final_name = filename + ".md"
    return os.path.join(local_dir, final_name)

async def crawl_all_docs(
    start_url: str,
    max_depth: int = None,
    output_dir: str = None,
    use_llm: bool = False
) -> None:
    """
    BFS: rastrea la doc y extrae Markdown, respetando estructura de carpetas.
    - start_url: URL principal
    - max_depth: nivel máximo de enlaces (default desde .env)
    - output_dir: carpeta raíz de salida (default desde .env)
    - use_llm: True => LLMContentFilter, False => PruningContentFilter
    """
    # Usar valores del .env como defaults
    if max_depth is None:
        max_depth = int(os.getenv("MAX_DEPTH", 2))
    if output_dir is None:
        output_dir = os.getenv("OUTPUT_DIR", "docs_outputs")

    parsed = urlparse(start_url)
    base_domain = parsed.netloc

    visited = set()
    to_crawl = [(start_url, 0)]

    browser_cfg = BrowserConfig(headless=True, verbose=False)

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

    os.makedirs(output_dir, exist_ok=True)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
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

            results = await crawler.arun_many(
                urls=batch_urls,
                config=run_cfg,
                dispatcher=dispatcher
            )
            for result in results:
                if result.success:
                    # Identificar la profundidad
                    idx = batch_urls.index(result.url)
                    current_depth = batch[idx][1]

                    # Markdown final (fit_markdown o raw)
                    if use_llm:
                        md = result.markdown_v2.fit_markdown or result.markdown
                    else:
                        md = result.markdown or ""

                    # Generar ruta local replicando path
                    local_md_file = build_local_filepath(output_dir, result.url)
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
                else:
                    print("[ERROR]", result.url, "=>", result.error_message)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Crawler BFS multi-url con subdirectorios")
    parser.add_argument("start_url", help="URL inicial (documentación)")
    parser.add_argument("--depth", type=int, help=f"Profundidad máxima (default={os.getenv('MAX_DEPTH', 2)})")
    parser.add_argument("--llm", action="store_true", help="Activar filtrado con LLMContentFilter")
    parser.add_argument("--out", help=f"Carpeta de salida para .md (default={os.getenv('OUTPUT_DIR', 'docs_outputs')})")
    return parser.parse_args()

async def main_cli():
    args = parse_args()
    await crawl_all_docs(
        start_url=args.start_url,
        max_depth=args.depth,
        output_dir=args.out,
        use_llm=args.llm
    )

if __name__ == "__main__":
    asyncio.run(main_cli())
