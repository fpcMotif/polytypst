"""Link titles and URL unwrapping shared by every cleaner."""

import re

_RESOLVED_LINKS = {
    "https://apple.news/AJTR4Hew8QSama-mtyy2Xpw": "https://www.politico.com/news/2026/03/19/trump-powell-fed-chair-doj-probe-warsh-00836447",
}
_LINK_TITLES = {
    "https://www.wallstreetoasis.com/resources/skills/strategy/shareholder-value": "Shareholder Value",
    "https://www.wallstreetoasis.com/forums/why-choose-sales-and-trading-over-investment-banking": "Why choose Sales and Trading over Investment Banking?",
    "https://www.wallstreetoasis.com/faq/what-are-the-best-qa-threads-and-interviews-with-top-finance-professionals-on-wso": "What are the best Q&A threads and interviews with top finance professionals on WSO?",
    "http://www.traders-library.com": "Traders’ Library",
    "http://govttrader.blogspot.com": "Govt Trader",
}
URL_TEXT = re.compile(r"(?:https?://|www\.)\S+")
BARE_URL = re.compile(r"(?<![(\[<\"/\w])https?://[^\s)\]>]*[^\s)\]>.,;:!?]")


def link_title(url: str) -> str | None:
    return _LINK_TITLES.get(url.split("#")[0].rstrip("/"))


def title_bare_url(m: re.Match[str]) -> str:
    title = link_title(m.group(0))
    return f"[{title}]({m.group(0)})" if title else m.group(0)


def unwrap_links(text: str, url: str, keep_web: bool = False) -> str:
    def label(m: re.Match[str]) -> str:
        before = text[m.start() - 1] if m.start() else ""
        after = text[m.end()] if m.end() < len(text) else ""
        lead = " " if before.isalnum() and m.group(1)[0].isalnum() else ""
        trail = " " if after.isalnum() and m.group(1)[-1].isalnum() else ""
        target = (m.group(2).split() or [""])[0]
        if keep_web and target.startswith("http"):
            target = _RESOLVED_LINKS.get(target, re.sub(r"[?&](?:cid|utm_\w+)=[^&]*$", "", target))
            return f"{lead}[{m.group(1)}]({target}){trail}"
        if URL_TEXT.fullmatch(m.group(1)) and target.startswith("http"):
            return lead + target + trail
        return lead + m.group(1) + trail

    return re.sub(rf"\[([^\]]+)\]\(({url})\)", label, text)


def plain_links(text: str) -> str:
    return re.sub(r"\[([^\]]*)\]\((?:[^()]|\([^()]*\))*\)", r"\1", text)
