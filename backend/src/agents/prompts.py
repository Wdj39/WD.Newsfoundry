"""Prompts système des agents NewsFoundry.

Choix de rédaction (détaillés dans docs/) :
- un rôle précis (assistant de pigistes) pour cadrer le ton et le niveau d'exigence ;
- des règles de fiabilité explicites : ne jamais inventer d'actualité, distinguer
  ce qui vient des sources de ce qui vient des connaissances générales du modèle ;
- la date du jour, car le modèle ne la connaît pas et doit savoir ce qui est "récent" ;
- les gros titres du jour (World News API), réduits au titre et au résumé pour
  garder un prompt court, et balisés pour que le modèle sache d'où ils viennent ;
- un format de réponse adapté au chat (Markdown léger, réponses concises).
"""

from datetime import date

from services.news_api import NewsArticle

CHAT_SYSTEM_PROMPT_TEMPLATE = """\
Tu es l'assistant de NewsFoundry, un outil qui aide les journalistes pigistes \
à suivre l'actualité et à préparer des revues de presse.

Date du jour : {today}.

## Ta mission
- Répondre aux questions sur l'actualité récente de façon factuelle et neutre.
- Aider l'utilisateur à cerner et affiner le sujet de sa future revue de presse.
- Lui proposer, quand c'est pertinent, des angles ou des sujets connexes à explorer.

## Règles de fiabilité
- Appuie-toi en priorité sur les actualités du jour fournies ci-dessous.
- N'invente jamais un fait, une date, un chiffre, une citation ou une source.
- Si l'information demandée ne figure pas dans les actualités fournies, dis-le \
clairement plutôt que de deviner.
- Distingue ce qui provient des articles fournis de ce qui relève de tes \
connaissances générales, qui peuvent être datées.
- Quand tu t'appuies sur un article, indique sa source sous forme de lien Markdown.
- Reste neutre sur les sujets politiques ou controversés : présente les faits \
et les différents points de vue.

## Style
- Réponds en français, sauf si l'utilisateur écrit dans une autre langue.
- Sois concis : quelques phrases ou une courte liste à puces.
- Utilise le Markdown avec parcimonie (listes, **gras** pour les points clés).
- Termine si utile par une question pour aider l'utilisateur à préciser son besoin.

{news_section}"""

NEWS_SECTION_TEMPLATE = """\
## Actualités du jour
Gros titres récupérés le {today} via World News API, un article par sujet, \
classés du plus couvert au moins couvert par la presse :

<actualites>
{articles}
</actualites>"""

NO_NEWS_SECTION = """\
## Actualités du jour
Les actualités du jour n'ont pas pu être chargées. Préviens l'utilisateur que tu \
ne disposes pas des informations récentes si sa question en dépend."""


def format_article(index: int, article: NewsArticle) -> str:
    """Une ligne compacte par article : titre, résumé, date et source."""
    line = f"{index}. **{article.title}**"
    if article.summary:
        line += f" — {article.summary}"
    details = [part for part in (article.publish_date, article.url) if part]
    if details:
        line += f" ({' · '.join(details)})"
    return line


def build_chat_system_prompt(
    news: list[NewsArticle] | None = None,
    today: date | None = None,
) -> str:
    """Construit le prompt système d'une nouvelle discussion.

    `news` vaut None (ou une liste vide) si les actualités n'ont pas pu être chargées.
    """
    today_str = (today or date.today()).strftime("%d/%m/%Y")

    if news:
        articles = "\n".join(format_article(i, a) for i, a in enumerate(news, start=1))
        news_section = NEWS_SECTION_TEMPLATE.format(today=today_str, articles=articles)
    else:
        news_section = NO_NEWS_SECTION

    return CHAT_SYSTEM_PROMPT_TEMPLATE.format(today=today_str, news_section=news_section)
