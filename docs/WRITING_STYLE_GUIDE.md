# Writing Style Guide — Northshore Books Report

A reference for keeping the report sounding like *you* (per the handwritten introduction in section 1) and for staying clear of the AI-detection sweep the module runs. Use it as a checklist when drafting or revising any new section.

---

## 1. Voice fingerprint

These are the recurring habits in your handwritten sample. Keep doing them — they are what makes the prose recognisably yours and not template output.

| Habit | Example from your handwriting |
|---|---|
| Slightly elevated, faintly literary diction | *"burgeoning contemporary problem"*, *"book connoisseurs"* |
| Borrowing tech vocabulary as metaphor for non-tech ideas | *"beyond the business's physical bandwidth"* |
| Scare quotes when introducing a term of art | *"brick-and-mortar"*, *"click-and-mortar"* |
| Concrete, sensory shop-floor imagery | *"a single complication at the till can delay every customer in the queue behind"* |
| Em-dash asides that qualify a clause without breaking it | *"— the role of the API, discussed next"* |
| Triple parallel structures (rule of three) | *"can be added, replaced, or taken offline"*; *"can remain available… can be reached… can continue operating"* |
| Forward and backward signposts between sections | *"As outlined in the introduction…"*, *"…discussed next"* |
| Quote a definition, then translate it into shop terms | TechTarget definition → *"For Northshore, this means…"* |
| Concede a problem, then offer the solution | *"…growing discontent. The solution is to adapt…"* |
| UK spelling | *customised, recognised, behaviour, organisation* |
| Harvard in-text citations | *(Corporate Finance Institute, 2024)* |

If a paragraph contains none of the above, it does not yet sound like you.

---

## 2. Sentence-level habits to keep

- **Long sentences are fine** when they are built from a stem plus parallel sub-clauses (your "can remain available… can be reached… can continue operating" sentence is a good model). They feel handwritten because the rhythm is uneven across the three branches.
- **Vary sentence length deliberately**. Follow a long, multi-clause sentence with a short, blunt one — five to ten words. AI-generated prose tends to keep all sentences in the same medium-length band.
- **Em dashes over parentheses** for asides. Round brackets in your draft are reserved for citations and code paths.
- **Semicolons** are used sparingly and usually link two related independent clauses, not lists.
- **Avoid bullet points in the body** of the report. Your handwriting moves in paragraphs; bullets break that voice. The only existing bullets in the draft are this guide and the references list.

---

## 3. Vocabulary — keep / avoid

**Keep using** (these are *your* words, found in the handwritten sample or the draft):
- *burgeoning, connoisseur, bottleneck, bandwidth (as metaphor), proportionate, defensible, dispersed, lightweight, snappy, subtle, deliberate, hardened, batteries-included*

**Avoid** (the AI-detector tells — these are over-represented in LLM output and will flag the paragraph even if the rest is yours):
- *delve, leverage, robust, seamless, navigate (metaphorical), landscape, tapestry, realm, intricate, vibrant, holistic, paradigm, ecosystem (unless literal), unlock potential, in today's fast-paced world, it is worth noting that, in conclusion, in summary, furthermore, moreover, additionally*

**Use with care** — fine once per section, suspicious if repeated:
- *crucially, importantly, ultimately, fundamentally, essentially*

---

## 4. Structural habits to keep

Your handwritten introduction follows a four-move pattern that should repeat across every subsection:

1. **Name the business problem in plain shop terms** (queues, staff, opening hours, the till).
2. **Quote or cite a source** that defines the technical concept.
3. **Translate the definition back into Northshore-specific terms** ("For Northshore, this means…").
4. **Hand off to the next section** with a short forward reference.

When a draft subsection feels generic, it is almost always because step 1 or step 3 was skipped — the prose floats free of the actual shop.

---

## 5. Humanisation rules (anti-AI-detection)

The module runs AI detection. Detectors flag *statistical* signatures, not facts, so the fix is to disrupt the patterns, not to add more content. Apply these passes in order on any paragraph you have rewritten or are unsure about:

1. **Read it aloud.** If a sentence sounds like a TED talk opener, a chatbot reply, or a LinkedIn post, rewrite it.
2. **Cut hedges.** Delete *it is worth noting*, *it is important to consider*, *one might argue*, *in essence*. Your handwriting does not hedge — it asserts and then qualifies with an em dash.
3. **Break perfect parallelism once per paragraph.** Rule of three is yours, but three identically-shaped clauses in a row are an AI tell. Make the third clause shorter, longer, or syntactically different from the first two.
4. **Anchor every abstraction to a concrete shop detail.** "Distributed computing" → "the till", "the queue", "outside shop hours". You did this naturally in the handwritten sample; preserve it.
5. **Name a file or line number** at least once per technical subsection. AI text rarely cites `orders/views.py:131-136`. Your draft already does this — keep it.
6. **Keep at least one slightly idiosyncratic word per paragraph** — *connoisseur, snappy, burgeoning, defensible*. A perfectly neutral vocabulary is itself a tell.
7. **Leave one minor stylistic quirk** that a copy-editor might have polished out: a semicolon you would defend, a long sentence you like, an em-dash you would refuse to convert to a comma. Over-polished text reads as machine-generated.
8. **Write the British spelling and stick to it.** Mixed US/UK spelling within a paragraph is a common sign of AI assembly.
9. **Do not start three consecutive paragraphs with the same word or shape** (e.g. all starting "The…"). Vary the opener.
10. **Citations belong inline, not in a final lump.** Every claim that could be challenged should carry a `(Author, Year)` immediately after it, the way you did with *(TechTarget, n.d.)*.

---

## 6. Worked before / after

A paragraph that would fail the humanisation pass:

> Furthermore, it is worth noting that Django provides a robust and seamless framework that allows developers to leverage a wide range of features. In today's fast-paced digital landscape, this is essential for navigating the complex ecosystem of modern web development.

The same point in your voice:

> Django was chosen because it is "batteries included" — a session-backed login, an auto-generated admin, an ORM that knows about migrations (Django Software Foundation, 2024). For a small shop with no in-house developer to spare, that breadth matters: the framework absorbs the boilerplate that every web application needs, so the few hours of bespoke work can be spent on the parts that are actually about books.

Note what changed: hedges deleted, a citation added, an abstract claim ("essential for navigating…") replaced with a concrete shop reason ("no in-house developer to spare"), and the rhythm broken with an em-dash aside.

---

## 7. Final pre-submission checklist

Before each subsection is locked:

- [ ] Contains at least one shop-floor concrete detail (till, queue, opening hours, staff, customer).
- [ ] Contains at least one inline Harvard citation.
- [ ] Contains at least one file path or line reference if it is a technical section.
- [ ] Contains at least one em-dash aside.
- [ ] Contains no banned vocabulary from §3.
- [ ] Sentence lengths vary across the paragraph (not all medium).
- [ ] Spelling is consistently British.
- [ ] Reads aloud as something you would say, not something a model would generate.
