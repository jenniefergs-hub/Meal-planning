# Kitchen Companion

A local web app that:

- Tracks ingredients you have on hand (added manually, or pulled from grocery receipt emails via Gmail).
- Stores recipes from books you own (with calories, ingredients, instructions).
- Recommends recipes — from your own collection and from the web (Spoonacular) — ranked by how many ingredients you already have, with calories shown for every recipe.
- Suggests flavor pairings — look up what goes with an ingredient, check compatibility across a combo of ingredients, or get pairing ideas based on your pantry.

## 1. Install

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run

```bash
python run.py
```

Open **http://localhost:8000**. Data is stored locally in `data/app.db` (SQLite) — nothing leaves your machine except the two optional API calls described below.

Use `http://localhost:8000`, not `127.0.0.1:8000` — it must match the Gmail redirect URI you register in step 4.

## 3. Add a Spoonacular API key (for online recipe recommendations + calories)

1. Sign up for a free key at https://spoonacular.com/food-api (free tier: 150 requests/day).
2. In the app, go to **Settings** and paste the key in, then Save.
3. On the **Recommendations** page, click "Find online recipes using my pantry".

Without a key, the app still works fully for your own pantry + recipe book — you just won't get live online suggestions.

## 4. Connect Gmail (to auto-import grocery receipts)

Live Gmail access requires you to register your own OAuth client with Google — there's no way around this, Google requires every app to have its own credentials.

1. Go to https://console.cloud.google.com/ and create (or pick) a project.
2. **APIs & Services → Library**: enable the **Gmail API**.
3. **APIs & Services → OAuth consent screen**: choose "External", fill in the required fields, and add your own email as a **test user** (this keeps the app private to you without needing Google's app-review process).
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application**
   - Authorized redirect URI: `http://localhost:8000/gmail/oauth2callback`
5. Download the client JSON (the "Download JSON" button after creating it).
6. In the app, go to **Settings**, paste the full JSON into the "Gmail connection" box, and Save.
7. Go to **Email Import** and click **Connect Gmail** — you'll see Google's consent screen (it may warn "Google hasn't verified this app" since it's your own private client; click **Advanced → Go to [app name] (unsafe)** to proceed — this is expected for personal-use OAuth apps).

The app only requests **read-only** Gmail access (`gmail.readonly`) and only fetches messages matching the search query you configure on the Email Import page (default: emails that look like order confirmations/receipts from the last 180 days). Narrow the query to your actual grocery retailer's sending address for best results, e.g. `from:instacart.com` or `from:orders@amazon.com`.

Click **Sync receipts now** to fetch and parse matching emails. Parsed line items land in a **Pending review** queue — receipt formats vary too much across retailers to trust automatic parsing blindly, so nothing is added to your pantry until you click **Approve** on each item (or **Reject** to discard it).

## 5. Using the app

- **Pantry**: your current ingredients — add manually, or approve items pulled from Gmail receipts.
- **Recipes**: your recipe book. Add recipes from cookbooks you own (title, book name, ingredients, instructions, servings, and **calories per serving**, which is required) or manually add an online recipe you like (paste the URL). On a recipe's page, click **"I made this"** to update your pantry (see below) and rate it.
- **Recommendations**: ranks your saved recipes by a mix of ingredient match and household ratings, and (with a Spoonacular key) searches the web for recipes matching your pantry, showing calories and missing ingredients for each.
- **Flavor Combos**: look up what pairs with a single ingredient, check compatibility across a comma-separated combo (e.g. `lemon, garlic, chicken`) and see what pairs with all of them at once, or browse suggestions generated from your current pantry — both "ready to combine" pairs you already have, and "consider adding" shopping ideas. Backed by a curated pairing dataset (`app/services/flavor_data.py`), not an external API, so it works offline and needs no key.
- **Settings**: household member names, Spoonacular API key, and Gmail credentials.

### Marking a recipe as cooked

On a recipe's page, click **"I made this — update my pantry"**. The app shows you which pantry items match the recipe's ingredients, pre-ticked; untick anything you didn't actually use up, then confirm. Ticked items are removed from your pantry entirely (quantities aren't tracked precisely enough to subtract partial amounts, e.g. "used 2 of the 6 eggs"), and the recipe's cooked count/date is updated.

### Ratings

Set up to 4 household member names in **Settings**. Each recipe page lets every member rate it 1–5 stars. Ratings feed into the **Recommendations** ranking (65% ingredient match, 35% average rating), so recipes your household rates highly get suggested more often; unrated recipes are scored neutrally so they aren't buried.

## 6. Deploying to Render (get a public link)

This app was built as **local-only and single-user, with no login system** — anything you deploy publicly is reachable by anyone with the URL, including any Spoonacular key or Gmail OAuth secret you've pasted into Settings. Only deploy it if you're comfortable with that, and set the Basic Auth env vars below so it isn't wide open.

1. Push this repo to GitHub (already done if you're reading this from your own fork).
2. In the [Render dashboard](https://dashboard.render.com/), **New → Blueprint**, and point it at this repo. Render will read `render.yaml` and provision a web service with a 1GB persistent disk (so your SQLite data survives restarts and redeploys).
3. Before the first deploy, set these environment variables on the service (Render will prompt for them since they're marked `sync: false` in the blueprint):
   - `BASIC_AUTH_USER` / `BASIC_AUTH_PASS` — a username/password Render will require via a browser prompt before serving any page. Strongly recommended.
4. Deploy. Render gives you a `https://<service-name>.onrender.com` URL.
5. If you use Gmail import, add `https://<your-render-url>/gmail/oauth2callback` as an **additional** authorized redirect URI on your Google OAuth client (Credentials → your client → Authorized redirect URIs) — the `localhost` one from step 4 above can stay too, so both local and hosted use work.
6. The free Render plan spins down after inactivity and cold-starts on the next request (a several-second delay) — upgrade to a paid plan for an always-on service.

Without `render.yaml`'s disk, Render's default filesystem is ephemeral and your pantry/recipes/settings would reset on every redeploy — the blueprint's `disk:` section avoids that by mounting persistent storage at `/var/data` (via the `DATA_DIR` env var, read in `app/database.py`).

## Notes and limitations

- **Receipt parsing is heuristic.** Grocery receipt emails have no standard format, so the parser looks for common patterns (quantity/name/price lines, HTML table rows) and flags blacklist words (tax, tip, delivery, total, etc.). It won't be perfect — that's why parsed items always go through the review queue before becoming pantry ingredients.
- **Calories for book recipes are entered by you** when you add the recipe, since there's no way to automatically look up calories for a recipe from a physical cookbook. Calories for online (Spoonacular) recommendations are fetched automatically.
- **"Cooked" pantry updates are all-or-nothing per item** — the app removes matched pantry ingredients entirely rather than subtracting partial quantities, since quantities are stored as free text (e.g. "2 lb", "a bunch") that can't be reliably subtracted.
- This is a single-user, local-only app — there's no login system, and ratings are attributed by household member name, not authenticated accounts. Don't expose it to the public internet as-is.
- `data/` and `credentials/` (your Gmail token and OAuth client secret) are gitignored and never committed.
