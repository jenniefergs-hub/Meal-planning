# Kitchen Companion

A web app (run locally on a computer, or deployed for free so it's reachable from any browser — see Section 6) that:

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
- **Recipes**: your recipe book. Add recipes from cookbooks you own (title, book name, ingredients, instructions, servings, and **calories per serving**, which is required) or manually add an online recipe you like (paste the URL). On a recipe's page, click **"I made this"** to update your pantry (see below) and rate it.
- **Recommendations**: ranks your saved recipes by a mix of ingredient match and household ratings, and (with a Spoonacular key) searches the web for recipes matching your pantry, showing calories and missing ingredients for each.
- **Settings**: household member names, Spoonacular API key, and Gmail credentials.

### Marking a recipe as cooked

On a recipe's page, click **"I made this — update my pantry"**. The app shows you which pantry items match the recipe's ingredients, pre-ticked; untick anything you didn't actually use up, then confirm. Ticked items are removed from your pantry entirely (quantities aren't tracked precisely enough to subtract partial amounts, e.g. "used 2 of the 6 eggs"), and the recipe's cooked count/date is updated.

### Ratings

Set up to 4 household member names in **Settings**. Each recipe page lets every member rate it 1–5 stars. Ratings feed into the **Recommendations** ranking (65% ingredient match, 35% average rating), so recipes your household rates highly get suggested more often; unrated recipes are scored neutrally so they aren't buried.

## 6. Deploying online (no computer needed, e.g. phone-only access)

If you don't have a computer, deploy the app to [Render](https://render.com)'s free tier instead of running it locally — the whole setup is done through a web browser, so it works from Safari on your iPhone.

### One-time setup

1. Go to https://render.com and sign up (free, no credit card required for the free tier).
2. Click **New +** → **Web Service**, connect your GitHub account, and select this repository (and branch).
3. Fill in:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips=*`
   - **Instance Type**: Free
4. Under **Environment Variables**, add:
   - `APP_PASSWORD` — a password you choose. **Required** — without it, anyone with the URL can open the app, since it's now on the public internet rather than your own computer.
   - `APP_USERNAME` — optional, defaults to `admin` if you skip it.
5. Click **Create Web Service**. The first build/deploy takes a few minutes; you'll get a URL like `https://kitchen-companion-xxxx.onrender.com`.
6. Open that URL in Safari — it'll prompt for the username/password you just set in step 4.

### Updating Spoonacular and Gmail for the new address

- **Spoonacular**: unchanged — go to the deployed app's Settings page and paste your key in.
- **Gmail**: `localhost` no longer applies, so add a second redirect URI:
  1. In Google Cloud Console → your OAuth client → add authorized redirect URI: `https://<your-render-url>/gmail/oauth2callback`
  2. On the deployed app's Settings page, paste the same client JSON and Save.
  3. Go to Email Import → Connect Gmail as before.

### Free-tier caveats

- **Sleeps when idle**: after 15 minutes with no visits, Render spins the app down. The next visit takes 30-60 seconds to wake it back up — that's expected, not broken.
- **Data resets on redeploy**: the free tier's disk isn't persistent across deploys, so pantry/recipe data is wiped whenever new code is pushed (not on ordinary sleep/wake cycles — only on an actual deploy). If that becomes a problem, ask for free persistent storage (e.g. via Neon's free Postgres tier) to be added — left out of this first pass to keep the initial deployment simple.

## Notes and limitations

- **Receipt parsing is heuristic.** Grocery receipt emails have no standard format, so the parser looks for common patterns (quantity/name/price lines, HTML table rows) and flags blacklist words (tax, tip, delivery, total, etc.). It won't be perfect — that's why parsed items always go through the review queue before becoming pantry ingredients.
- **Calories for book recipes are entered by you** when you add the recipe, since there's no way to automatically look up calories for a recipe from a physical cookbook. Calories for online (Spoonacular) recommendations are fetched automatically.
- **"Cooked" pantry updates are all-or-nothing per item** — the app removes matched pantry ingredients entirely rather than subtracting partial quantities, since quantities are stored as free text (e.g. "2 lb", "a bunch") that can't be reliably subtracted.
- This is a single-user app — ratings are attributed by household member name, not authenticated accounts, and there's only one shared password for the whole app (see the deployment section if running it publicly), not per-person logins.
- `data/` and `credentials/` (your Gmail token and OAuth client secret) are gitignored and never committed.
- If deployed publicly (Section 6), set `APP_PASSWORD` (and optionally `APP_USERNAME`) as environment variables on the host — never commit them to the repo. Locally, if these aren't set, the app runs without a password prompt, same as before.
