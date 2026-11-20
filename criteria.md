# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Four of five allows for occasional keyword phrasing misses in the plain search
without treating normal model variation as four separate bugs. A simple match
cannot understand every synonym, so 5 of 5 would demand more semantics than this
tool currently guarantees.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
The impossible-query branch depends on one deterministic list result, not on
model wording. It should stop every time, and a miss would expose a broken branch
rather than a borderline search interpretation.

---

## 3. The selected item stays consistent across the loop

For 5 of 5 matching runs, `session["selected_item"]["id"]` is the ID of the
first item in `session["search_results"]`, and that same ID is included in the
trace input for `suggest_outfit`.

**Why this target:**
A full pass requires that state, not just a successful model response. The
first-result rule is simple and deterministic, so one mismatch is enough to
identify a state handoff bug without judging model wording.



---

## 4. The fit card is complete and caption-sized

For at least 4 of 5 completed runs, the fit card contains 2 to 4 sentences and
mentions the selected item's title, exact price, and platform. It must not
contain an empty string or only an item-description fragment.

**Why this target:**
Model wording will vary, so wording similarity is a poor automated test. These
four structural checks catch unusable cards while allowing natural variation.



---

## 5. Search honors the price ceiling

For 5 of 5 queries that include a price ceiling, every result returned by
`search_listings` has `price <= the ceiling`, inclusive.

**Why this target:**
A price filter is a deterministic tool constraint and is easy to verify. Requiring
all results to pass means one overpriced listing fails the criterion even if the
rest of the run succeeds.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
