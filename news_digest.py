import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests


BASE_DIR = Path(__file__).resolve().parent
FEEDS_FILE = BASE_DIR / "feeds.json"
USER_AGENT = "NewsDigest/1.0 (RSS reader)"


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def summarize(value, max_sentences=2, max_characters=400):
    text = clean_text(value)
    if not text:
        return "Resumo não disponível no feed."

    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:max_sentences])
    if len(summary) > max_characters:
        summary = summary[: max_characters - 1].rsplit(" ", 1)[0] + "…"
    return summary


def published_at(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    return None


def load_feeds():
    with FEEDS_FILE.open(encoding="utf-8") as feeds_file:
        return json.load(feeds_file)


def collect_news(feeds, topics, limit):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    news = []
    seen_links = set()

    for topic in topics:
        for source in feeds.get(topic, []):
            try:
                response = session.get(source["url"], timeout=15)
                response.raise_for_status()
                parsed_feed = feedparser.parse(response.content)
            except requests.RequestException as error:
                print(f"Aviso: não foi possível consultar {source['nome']}: {error}", file=sys.stderr)
                continue

            if parsed_feed.bozo and not parsed_feed.entries:
                print(f"Aviso: feed inválido ou vazio em {source['nome']}.", file=sys.stderr)
                continue

            for entry in parsed_feed.entries:
                link = entry.get("link", "").strip()
                title = clean_text(entry.get("title", ""))
                if not title or (link and link in seen_links):
                    continue
                if link:
                    seen_links.add(link)

                description = entry.get("summary", "")
                if not description and entry.get("content"):
                    description = entry.content[0].get("value", "")

                news.append(
                    {
                        "tema": topic,
                        "fonte": source["nome"],
                        "titulo": title,
                        "resumo": summarize(description),
                        "link": link,
                        "publicado": published_at(entry),
                    }
                )

    news.sort(key=lambda item: item["publicado"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return news[:limit]


def render_markdown(news):
    if not news:
        return "Nenhuma notícia encontrada nos feeds selecionados."

    lines = ["# Resumo de notícias", ""]
    for item in news:
        date = item["publicado"].strftime("%d/%m/%Y %H:%M UTC") if item["publicado"] else "data não informada"
        lines.extend(
            [
                f"## {item['titulo']}",
                f"**Tema:** {item['tema']} | **Fonte:** {item['fonte']} | **Publicado:** {date}",
                "",
                item["resumo"],
            ]
        )
        if item["link"]:
            lines.append(f"\n[Leia a notícia]({item['link']})")
        lines.append("")
    return "\n".join(lines).rstrip()


def main():
    parser = argparse.ArgumentParser(description="Gera um resumo de notícias a partir de feeds RSS.")
    parser.add_argument(
        "--tema",
        choices=["todos", "tecnologia", "esportes"],
        default="todos",
        help="Tema das notícias (padrão: todos).",
    )
    parser.add_argument("--limite", type=int, default=5, help="Quantidade máxima de notícias (padrão: 5).")
    parser.add_argument("--saida", type=Path, help="Arquivo Markdown de saída; sem esta opção, imprime no terminal.")
    args = parser.parse_args()

    if args.limite < 1:
        parser.error("--limite deve ser maior que zero.")

    try:
        feeds = load_feeds()
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"não foi possível carregar {FEEDS_FILE.name}: {error}")

    topics = list(feeds) if args.tema == "todos" else [args.tema]
    markdown = render_markdown(collect_news(feeds, topics, args.limite))

    if args.saida:
        args.saida.write_text(markdown + "\n", encoding="utf-8")
        print(f"Resumo salvo em {args.saida}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()