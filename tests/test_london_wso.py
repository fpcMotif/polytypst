from polytypst.books import module

clean_wso_thread = module("london_treasury", "wso").clean_wso_thread

ANON_THREAD = """# What do you do?

[](https://www.wallstreetoasis.com/forum/trading/what-do-you-do)

[CF](https://www.wallstreetoasis.com/page/user-industry-status "Corporate Finance - 1st Year Analyst")

Analyst 1 in CorpFin

5y

I straight up asked a trader this question.
"""

PLAIN_THREAD = """Home
 Forums
 Sales and Trading Forum
Jun 20, 2013
Q&A: Rates Trader Taking Your Questions
Maximus
ST
Subscribe
Share

Ask me anything.

12 Comments
\xa0
JWick
PE
13y

Hi,

Why did you choose rates?

Reply
Quote
Report
Other
Authored by: Certified Private Equity Professional
[-]
\xa0
Maximus
ST
13y
JWickHi,

Why did you choose rates?

I have always been a macro guy.

Reply
Quote
Report
Other
\xa0
Maximus
ST
13y
PMHey man, thanks for the Q&A.

Reply
Quote
Report
Other
"""


def test_anonymous_poster_becomes_card_without_letter_badge() -> None:
    text = clean_wso_thread(ANON_THREAD, "What do you do?")
    assert "**@anon/Analyst 1 in CorpFin:**" in text
    assert "CF" not in text.split()


def test_plain_layout_posters_become_cards() -> None:
    text = clean_wso_thread(PLAIN_THREAD, "")
    assert text.startswith("# Q&A: Rates Trader Taking Your Questions\n\n**@monkey/Maximus:**")
    assert "**@monkey/JWick:**" in text
    assert not any(line.strip() in {"ST", "PE", "13y", "Reply", "Authored by: Certified Private Equity Professional"} for line in text.splitlines())


def test_plain_layout_quote_keeps_its_full_extent() -> None:
    text = clean_wso_thread(PLAIN_THREAD, "")
    assert "> Hi,\n\n> Why did you choose rates?\n\nI have always been a macro guy." in text
    assert "JWickHi" not in text
    assert "*PM:* Hey man, thanks for the Q&A." in text
