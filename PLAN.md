# Pantry-to-Plate: Development Plan

An app that builds a live inventory of ingredients from your grocery receipt
emails, and recommends recipes — from your own cookbooks and the online
recipes you save — that you can actually make with what's in the house,
each one annotated with calories.

## 1. Core loop

```
Receipt emails ──▶ Ingredient inventory ──┐
                                           ├──▶ Recipe matcher/ranker ──▶ Recommendations (+ calories)
Cookbooks + saved recipes ──▶ Recipe DB ──┘
```

Three pipelines feed one matching engine. Each pipeline can be built and
tested independently, which is how the phases below are sequenced.

## 2. Data model (high level)

- **Ingredient** — canonical name, category, unit, optional USDA/nutrition ID
- **PantryItem** — ingredient ref, quantity, unit, purchase date, source
  receipt, estimated use-by, status (in_stock / low / used_up)
- **Recipe** — title, source (book title/page or URL), servings, prep/cook
  time, tags, ingredient lines, steps, calories/serving, calories total
- **RecipeIngredientLine** — raw text ("2 tbsp olive oil") + parsed
  quantity/unit + resolved Ingredient ref (nullable until matched)
- **Receipt** — email id, retailer, order date, raw line items, parse
  status, parsed PantryItems

## 3. The three pipelines

### 3a. Pantry from receipt emails
- Gmail API (OAuth, read-only scope, filtered by label/sender) — no bulk
  mailbox scraping. User selects which retailer senders to watch.
- Per-retailer HTML/text parsing where feasible (stable formats: Tesco,
  Ocado, Amazon Fresh, Instacart, etc.), falling back to an LLM extraction
  pass (receipt text → structured JSON line items) for anything else.
- Normalize noisy product names ("Tesco British Semi Skimmed 2L") to a
  canonical ingredient ("milk") via a lookup table + LLM fallback.
- Perishability model: category-based shelf-life defaults (dairy ~7d,
  produce ~5d, tinned goods ~months) to estimate use-by, refined later by
  user corrections. This is a heuristic, not a promise — the UI should let
  users mark items "used up" or "still have it" to keep inventory honest.

### 3b. Recipes from cookbooks you own
- Photo capture of a recipe page → OCR (Claude vision, since it handles
  varied cookbook layouts better than plain OCR) → structured recipe JSON
  (title, ingredients, steps, servings).
- User reviews/corrects the parse once, then it's stored permanently —
  this is a one-time digitization cost per recipe, not a repeated scan.

### 3c. Recipes from online sources you use
- Paste a URL → scrape. Most recipe sites embed schema.org/Recipe
  JSON-LD, so a library like `recipe-scrapers` (Python, covers 100+ sites)
  handles the majority; LLM extraction as fallback for the rest.

### 3d. Calories
- Resolve each recipe ingredient line to a nutrition DB entry (USDA
  FoodData Central — free, no rate-limit concerns) and sum
  quantity × kcal/100g, divided by servings for calories/serving.
- Ambiguous matches (a resolved ingredient with no confident nutrition
  match) get flagged in the UI rather than silently guessed.

## 4. Recommendation engine

Given current pantry state, score each recipe by:
1. **Coverage** — % of ingredient lines resolvable from what's in stock
2. **Expiry urgency** — boost recipes using items expiring soonest ("use
   it up" mode, directly reduces food waste — a natural motivating hook)
3. **Calorie fit** — optional filter/target if the user sets a calorie
   range
4. Missing-ingredient recipes still show, with a "you need: X, Y" list,
   so the app is useful even at partial pantry coverage.

## 5. Suggested stack

- **Backend**: Python + FastAPI — natural fit given OCR/LLM extraction
  and email parsing all lean on Python tooling.
- **DB**: Postgres.
- **Frontend**: Next.js PWA — mobile-first, since the app gets used
  standing in the kitchen.
- **Background jobs**: scheduled worker for email sync (e.g. every few
  hours) rather than polling on page load.
- **External services**: Gmail API, USDA FoodData Central API,
  `recipe-scrapers`, Claude (vision for cookbook OCR + extraction
  fallback for receipts/recipes).

## 6. Privacy notes (email access is the sensitive part)

- Request the narrowest Gmail scope (`gmail.readonly`, ideally filtered
  to specific labels the user sets up), never full mailbox access.
- Store only parsed line items + a reference, not full raw email bodies,
  once parsing succeeds.
- Make the retailer-sender allowlist explicit and user-editable.

## 7. Phased roadmap

| Phase | Deliverable |
|---|---|
| 0 | Data models, project scaffold, auth |
| 1 | Recipe management: manual entry + URL import + calorie calc |
| 2 | Pantry from email: Gmail OAuth, retailer parsers, inventory UI |
| 3 | Recommendation engine: coverage scoring, expiry-aware ranking |
| 4 | Cookbook digitization: photo capture → OCR → recipe review flow |
| 5 | Polish: shopping list generation for missing ingredients, meal
      planning calendar |

Phases 1 and 2 can run in parallel — they don't depend on each other,
only phase 3 depends on both.

## 8. Open questions to settle before building

- Which retailers' receipt emails to support first (affects parser
  priority)?
- Any dietary constraints/allergies to factor into recommendations?
- Solo use or household (shared pantry/recipes)?
