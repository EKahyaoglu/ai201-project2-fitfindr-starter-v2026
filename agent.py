"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    The loop parses the query, searches local listings, and records every
    handoff in session state and the trace. It stops on empty search results or
    model-unavailable errors instead of continuing with invalid state.
    """
    session = new_session(query, wardrobe)
    trace.start_trace()

    price_match = re.search(r"(?:under|below|max(?:imum)?(?: price)?|\$)\s*\$?(\d+(?:\.\d+)?)", query, re.I)
    max_price = float(price_match.group(1)) if price_match else None

    size_match = re.search(r"(?:\bsize\s+|\bin\s+)([A-Za-z0-9]+(?:/[A-Za-z0-9]+)?)", query, re.I)
    size = size_match.group(1).upper() if size_match else None

    description = re.sub(r"\b(?:under|below|max(?:imum)?(?: price)?)[^,]*", " ", query, flags=re.I)
    description = re.sub(r"\b(?:size|in)\s+[A-Za-z0-9]+(?:/[A-Za-z0-9]+)?", " ", description, flags=re.I)
    description = re.sub(r"\$\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"\s+", " ", description).strip()

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }
    trace.step("parse_query", inputs=query, returned=session["parsed"])

    for iteration in range(1, config.MAX_ITERATIONS + 1):
        trace.check_iterations(iteration)

        try:
            results = search_listings(description, size=size, max_price=max_price)
        except Exception as exc:
            session["error"] = f"Search could not be completed: {exc}"
            trace.step("search_listings", inputs=session["parsed"], returned=[], note="branch: search error")
            return session

        session["search_results"] = results
        trace.step("search_listings", inputs=session["parsed"], returned=results)

        if not results:
            changes = []
            if size:
                changes.append(f"a different size than {size}")
            if max_price is not None:
                changes.append(f"a price above ${max_price:g}")
            changes.append("a broader description")
            session["error"] = "No matching listings. Try " + " or ".join(changes) + "."
            trace.step("planning_branch", returned="stop", note="branch: empty results, do not call more tools")
            return session

        session["selected_item"] = results[0]
        trace.step("select_item", inputs=results, returned=session["selected_item"])

        try:
            outfit = suggest_outfit(session["selected_item"], wardrobe)
        except ModelUnavailable as exc:
            session["error"] = f"The styling model is unavailable: {exc}"
            trace.step("suggest_outfit", returned="", note="branch: model unavailable")
            return session

        session["outfit_suggestion"] = outfit.strip() if isinstance(outfit, str) else ""
        trace.step("suggest_outfit", inputs=session["selected_item"], returned=session["outfit_suggestion"])

        try:
            card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
        except ModelUnavailable as exc:
            session["error"] = f"The fit-card model is unavailable: {exc}"
            trace.step("create_fit_card", returned="", note="branch: model unavailable")
            return session

        session["fit_card"] = str(card).strip()
        trace.step("create_fit_card", inputs={
            "outfit": session["outfit_suggestion"],
            "item": session["selected_item"],
        }, returned=session["fit_card"])
        return session

    session["error"] = "The planning loop exceeded its iteration limit."
    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
