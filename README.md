# Dada Group Academy: AI Onboarding Assistant

A learning assistant for new employees' first 90 days, built for the GJU × Dada Group AI Challenge (German Week 2026).

> Company facts are paraphrased from supplied competition materials. Scenarios and the learning plan are fictional training examples, not official Dada Group procedures. The assistant does not make employment decisions.

## Features

1. **Welcome and track choice:** Sales or Delivery.
2. **Question-answer assistant:** answers only from the knowledge base, shows the source ID (K01-K18) with every answer, gives partial answers when only part is known, and refuses when the information isn't available.
3. **Practice scenarios:** three per track, with 1-5 feedback linked to one of Dada Group's five values.
4. **Suggested 90-day learning plan:** Days 1-7, Day 30, Day 60, Day 90, plus a knowledge quiz.
5. **Progress tracking:** tick milestones, complete scenarios and the quiz, see a completion percentage.

The chat also understands "a customer asks..." (starts a scenario) and "I completed Day 30" (updates progress).

## How it works

1. **Search (local):** the question is compared with all 18 facts using a multilingual embedding model (`intfloat/multilingual-e5-small`) that runs on this computer.
2. **Answer (Gemini):** the top 5 facts and the question are sent to Gemini, which must answer only from those facts and return the IDs it used.
3. **Checks (code):** cited IDs not given to Gemini are removed; an answer with no valid source becomes a refusal.
4. **Fallback:** if Gemini is busy or offline, the app tries a backup model, then shows the closest fact only if the match is very strong, otherwise refuses.

## Setup

Requires Python 3.13 and a free Gemini API key from https://aistudio.google.com

```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and put your key in it:

```
GEMINI_API_KEY=your-key-here
```

## Run

```
python -m streamlit run app.py
```

The first start downloads the embedding model (about 470 MB). After that it works offline, except for Gemini answers.

## Tests

```
python run_tests.py
```

Runs 39 tests (the jury test cases, the sample FAQ, extra tricky questions, routing and scenario feedback) and saves the results to `results/`. The latest results are also shown on the app's **Data & sources** page.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface: pages, chat, sidebar |
| `data_loader.py` | Loads the CSVs, reloads them when edited, checks links between files |
| `retrieval.py` | Arabic normalization, keyword search, AI search by meaning |
| `qa.py` | Gemini prompt, answering pipeline, fallback |
| `scenarios.py` | Scenario feedback |
| `router.py` | Decides if a chat message is a question, a scenario or a progress update |
| `progress.py` | Activities and completion percentage |
| `run_tests.py` | Automatic tests and results file |
| `data/` | Competition dataset |

## Privacy

- No user accounts; the optional first name and all progress stay in the browser session and are never saved to a file.
- Search runs locally. Only the question and the 5 retrieved facts are sent to Gemini, never the whole knowledge base.
- The API key is kept in `.env`, which is excluded from Git.

## Limitations

- Progress resets when the page is refreshed.
- Keyword routing can misfire (for example, a question containing "عميل" may start a scenario); see tests I04 and I05.
- Answers depend on Gemini's free tier, which can be slow or busy; the fallback is less fluent.
- On the free tier, Google may use the content sent to improve its models.