# Kitchen Companion

A local web app that:

- Tracks ingredients you have on hand (added manually, or pulled from grocery receipt emails via Gmail).
- Stores recipes from books you own (with calories, ingredients, instructions).
- Recommends recipes — from your own collection and from the web (Spoonacular) — ranked by how many ingredients you already have, with calories shown for every recipe.

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
- **Recipes**: your recipe book. Add recipes from cookbooks you own (title, book name, ingredients, instructions, servings, and **calories per serving**, which is required) or manually add an online recipe you like (paste the URL).
- **Recommendations**: ranks your saved recipes by percentage of ingredients you currently have in your pantry, and (with a Spoonacular key) searches the web for recipes matching your pantry, showing calories and missing ingredients for each.
- **Settings**: API key and Gmail credentials.

## Notes and limitations

- **Receipt parsing is heuristic.** Grocery receipt emails have no standard format, so the parser looks for common patterns (quantity/name/price lines, HTML table rows) and flags blacklist words (tax, tip, delivery, total, etc.). It won't be perfect — that's why parsed items always go through the review queue before becoming pantry ingredients.
- **Calories for book recipes are entered by you** when you add the recipe, since there's no way to automatically look up calories for a recipe from a physical cookbook. Calories for online (Spoonacular) recommendations are fetched automatically.
- This is a single-user, local-only app — there's no login system. Don't expose it to the public internet as-is.
- `data/` and `credentials/` (your Gmail token and OAuth client secret) are gitignored and never committed.
