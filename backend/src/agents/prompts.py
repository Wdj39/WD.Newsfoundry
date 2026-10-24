"""Prompts système des agents NewsFoundry.

Choix de rédaction (détaillés dans docs/) :
- un rôle précis (assistant de pigistes) pour cadrer le ton et le niveau d'exigence ;
- des règles de fiabilité explicites : ne jamais inventer d'actualité, distinguer
  ce qui vient des sources de ce qui vient des connaissances générales du modèle ;
- la date du jour, car le modèle ne la connaît pas et doit savoir ce qui est "récent" ;
- les gros titres du jour (World News API), réduits au titre et au résumé pour
  garder un prompt court, et balisés pour que le modèle sache d'où ils viennent ;
- des consignes sur quand et comment utiliser l'outil `search_news` ;
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

## Recherche d'articles
- Tu disposes de l'outil `search_news` pour charger des articles récents.
- Utilise-le quand l'utilisateur veut approfondir un sujet, ou quand les \
actualités du jour ci-dessous ne suffisent pas pour répondre.
- Formule des requêtes courtes (2 à 5 mots-clés) ; lance une nouvelle recherche \
avec d'autres mots-clés si la première ne donne rien.

## Règles de fiabilité
- Appuie-toi en priorité sur les actualités du jour et sur les articles trouvés \
avec `search_news`.
- N'invente jamais un fait, une date, un chiffre, une citation ou une source.
- Si l'information demandée ne figure ni dans les actualités fournies ni dans \
les articles trouvés, dis-le clairement plutôt que de deviner.
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


# --- Agent de revue de presse ------------------------------------------------

REVIEW_INSTRUCTIONS = """\
Tu es rédacteur en chef pour NewsFoundry. À partir d'une discussion entre un \
journaliste et l'assistant, tu rédiges une revue de presse sur le thème demandé.

## Règles
- Utilise uniquement les informations et les articles présents dans la discussion \
fournie : n'invente aucun fait, chiffre, citation, article ni URL.
- Ne retiens que les articles en rapport avec le thème demandé. Recopie les URL \
à l'identique.
- Si la discussion contient peu d'éléments sur le thème, produis une revue courte \
et signale-le dans la synthèse plutôt que de compléter avec des suppositions.
- Reste factuel et neutre ; présente les différents points de vue s'il y en a.
- Rédige en français, dans un style journalistique clair.
"""


def build_review_prompt(topic: str, conversation: str) -> str:
    """Message envoyé à l'agent de revue de presse.

    La discussion est placée entre balises pour que le modèle distingue
    clairement la consigne des données à synthétiser.
    """
    return (
        f"Thème de la revue de presse : {topic}\n\n"
        f"<discussion>\n{conversation}\n</discussion>"
    )
