# Resumo de notícias

Script em Python que consulta feeds RSS de portais de notícias e gera um resumo
em Markdown das notícias de tecnologia e esportes. Ele usa as descrições
publicadas nos feeds, sem chave de API.

## Requisitos

- Python 3.10 ou superior
- Acesso à internet para consultar os feeds

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

## Uso

```bash
python news_digest.py
python news_digest.py --tema tecnologia
python news_digest.py --tema esportes --limite 10 --saida esportes.md
```

O relatório é exibido no terminal por padrão. Use `--saida` para salvá-lo em
arquivo. As fontes e seus temas ficam em `feeds.json`; você pode editar essa
lista para adicionar ou remover feeds RSS.

Se um portal estiver indisponível ou não oferecer um feed compatível, o script
avisa e continua com as demais fontes. As descrições e os links continuam
sendo conteúdo dos respectivos portais.
