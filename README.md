# Kitchen Companion

A web app (run locally on a computer, or deployed for free so it's reachable from any browser — see Section 7) that:

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

Open **http://localhost:8000**. Data is stored locally in `data/app.db` (SQLite) — nothing leaves your machine except the two optional API calls described below. (If a `DATABASE_URL` environment variable is set, the app uses that Postgres database instead — see Section 7's persistent storage step for deployed use; you don't need this locally.)

Use `http://localhost:8000`, not `127.0.0.1:8000` — it must match the Gmail redirect URI you register in step 4.

## 3. Add a Spoonacular API key (for online recipe recommendations + calories)

1. Sign up for a free key at https://spoonacular.com/food-api (free tier: 150 requests/day).
2. In the app, go to **Settings** and paste the key in, then Save.
3. On the **Recommendations** page, click "Find online recipes using my pantry".

Without a key, the app still works fully for your own pantry + recipe book — you just won't get live online suggestions.

## 4. Add an OCR key (for importing recipes from photos)

Two options — set up one (or both, in which case Google Cloud Vision is used automatically):

**Google Cloud Vision (recommended, more accurate):**
1. In the same Google Cloud project you'll use for Gmail (Section 5), go to **APIs & Services → Library**, search "Cloud Vision API", and enable it. This requires linking a billing account (card) to the project — the free tier (1,000 images/month) comfortably covers personal use, and you can set a budget alert under Billing as a safety net.
2. **APIs & Services → Credentials → Create Credentials → API key**. Optionally restrict it to just "Cloud Vision API" under API restrictions.
3. In the app, go to **Settings**, paste the key into "Google Cloud Vision API key", Save.

**OCR.space (free alternative, no card, lower accuracy):**
1. Sign up for a free key at https://ocr.space/ocrapi (no credit card required).
2. In the app, go to **Settings**, paste the key into "OCR.space API key", Save.

Either way: on the **Recipes** page, click "Import from a URL or photo" → upload a photo.

Without either key, importing from a **URL** still works (it doesn't need this) — you'll just see a message if you try the photo option without one set up.

## 5. Connect Gmail (to auto-import grocery receipts)

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

## 6. Using the app

- **Pantry**: your current ingredients — add manually, or approve items pulled from Gmail receipts.
- **Recipes**: your recipe book. Add recipes from cookbooks you own (title, book name, ingredients, instructions, servings, and **calories per serving**, which is required), manually add an online recipe you like (paste the URL), or import from a URL or photo (see below). Click **"Edit recipe"** on any recipe's page to fix or update it later — handy for cleaning up an import that didn't come through perfectly. On a recipe's page, click **"I made this"** to update your pantry (see below) and rate it.
- **Recommendations**: ranks your saved recipes by a mix of ingredient match and household ratings, and (with a Spoonacular key) searches the web for recipes matching your pantry, showing calories and missing ingredients for each. Any oil, salt, and seasoning pepper (not bell/chili peppers) are ignored when scoring matches and listing what's missing, since those are assumed to always be on hand.
- **Settings**: household member names, Spoonacular API key, OCR API key, and Gmail credentials.

### Importing a recipe from a URL or photo

On the **Recipes** page, click **"Import from a URL or photo"**.

- **From a URL**: paste a link to any recipe page. The app first tries the structured recipe data most modern recipe sites embed (schema.org markup) to reliably pull the title, ingredients, instructions, servings, and prep time — plus calories, if the site happens to publish them (many don't). If a page doesn't have that structured data, it automatically falls back to a rough guess based on the page's visible text (title from the page heading, ingredient lines identified by starting with a quantity, everything else treated as instructions) — much less reliable, and clearly flagged as such on the review page, but means most pages return *something* to start from rather than nothing.
- **From a photo**: upload a photo of a cookbook page (needs the OCR.space key from Section 4). The app reads the text and makes a rough guess at splitting it into a title, ingredient lines, and instructions, based on which lines start with a quantity. This is much less reliable than the URL import — cookbook layouts vary a lot — so review it carefully.

Either way, you land on a pre-filled version of the "Add a recipe" form before anything is saved — nothing is added to your recipe book until you review and click **Save recipe**. Calories are almost never available from either source, so that field is usually left for you to fill in.

### Calculating calories from ingredients

On a recipe's page, click **"Calculate calories from ingredients"** (needs a Spoonacular key from Section 3). The app looks up nutrition for each ingredient by name and quantity, sums the calories, and divides by the recipe's servings. You'll see a breakdown of what was matched (and a warning if any ingredient couldn't be matched, which counts as 0 calories in the total) — if any ingredient's figure looks wrong, edit it right there and the total and per-serving numbers recalculate live; you can also type a final number directly. Nothing is applied to the recipe until you click Save. Handy for recipes imported from a photo, or any recipe where you don't already know the calorie count.

### Emailing a recipe

Click **"Email this recipe"** on any recipe's page — it opens your device's own mail app with the recipe (title, servings, calories, ingredients, and instructions) pre-filled as the subject and body; you just add a recipient and hit send. This uses a plain `mailto:` link rather than sending from the app itself, so it needs no setup, no API key, and doesn't touch your Gmail connection at all.

### Marking a recipe as cooked

On a recipe's page, click **"I made this — update my pantry"**. The app shows you which pantry items match the recipe's ingredients, pre-ticked; untick anything you didn't actually use up, then confirm. Ticked items are removed from your pantry entirely (quantities aren't tracked precisely enough to subtract partial amounts, e.g. "used 2 of the 6 eggs"), and the recipe's cooked count/date is updated.

### Ratings

Set up to 4 household member names in **Settings**. Each recipe page lets every member rate it 1–5 stars. Ratings feed into the **Recommendations** ranking (65% ingredient match, 35% average rating), so recipes your household rates highly get suggested more often; unrated recipes are scored neutrally so they aren't buried.

**Top Recipes by Person** (linked from the Recipes page) shows each household member's own top 20 rated recipes, highest to lowest — handy for settling "what does everyone actually like" separately from the blended household ranking.

### Units

When adding or editing an ingredient (in the Pantry or on a recipe), the unit field is a dropdown of common cooking units (g, cup, tbsp, can, etc.) rather than free text, so units stay consistent. Pick **"Other…"** to type a custom unit if what you need isn't listed.

## 7. Deploying online (no computer needed, e.g. phone-only access)

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

### Persistent storage (so data survives redeploys)

By default the app stores data in a local SQLite file, which works fine locally but doesn't survive a Render redeploy (Render's free-tier disk is wiped on every new deploy). To keep your pantry and recipes permanently, point the app at a free hosted Postgres database instead — this only takes a few minutes and is entirely browser-based:

1. Go to https://neon.tech and sign up (free tier, no credit card required, no expiry).
2. Create a new project (any name, any region).
3. On the project dashboard, copy the **connection string** — it looks like `postgresql://user:password@ep-xxxx.aws.neon.tech/neondb?sslmode=require`.
4. Back in Render, open your web service → **Environment** → add a variable:
   - `DATABASE_URL` — paste the Neon connection string.
5. Render will automatically redeploy with the new variable. From then on, all your data lives in Neon's Postgres — it survives Render redeploys, restarts, and sleep/wake cycles indefinitely.

If you skip this step, the app still works fine on Render — your data just resets each time new code is deployed (see caveats below).

### Updating Spoonacular and Gmail for the new address

- **Spoonacular**: unchanged — go to the deployed app's Settings page and paste your key in.
- **Gmail**: `localhost` no longer applies, so add a second redirect URI:
  1. In Google Cloud Console → your OAuth client → add authorized redirect URI: `https://<your-render-url>/gmail/oauth2callback`
  2. On the deployed app's Settings page, paste the same client JSON and Save.
  3. Go to Email Import → Connect Gmail as before.

### Free-tier caveats

- **Sleeps when idle**: after 15 minutes with no visits, Render spins the app down. The next visit takes 30-60 seconds to wake it back up — that's expected, not broken.
- **Data resets on redeploy unless you set up `DATABASE_URL`** (see above): without it, the free tier's local disk isn't persistent across deploys, so pantry/recipe data is wiped whenever new code is pushed (not on ordinary sleep/wake cycles — only on an actual deploy). With a Neon `DATABASE_URL` set, this doesn't apply — data is permanent.

## Notes and limitations

- **Receipt parsing is heuristic.** Grocery receipt emails have no standard format, so the parser looks for common patterns (quantity/name/price lines, HTML table rows) and flags blacklist words (tax, tip, delivery, total, etc.). It won't be perfect — that's why parsed items always go through the review queue before becoming pantry ingredients.
- **Calories for book recipes are entered by you** when you add the recipe, since there's no way to automatically look up calories for a recipe from a physical cookbook. Calories for online (Spoonacular) recommendations are fetched automatically.
- **URL and photo recipe import are also best-effort.** URL import relies on the page publishing structured recipe data (most modern recipe blogs do; older or unusual sites may not). Photo import depends on OCR quality and a simple "does this line start with a number" heuristic to separate ingredients from instructions, which won't handle every cookbook layout well. Both land in an editable review form before saving, specifically because neither is reliable enough to trust unattended.
- **"Cooked" pantry updates are all-or-nothing per item** — the app removes matched pantry ingredients entirely rather than subtracting partial quantities, since quantities are stored as free text (e.g. "2 lb", "a bunch") that can't be reliably subtracted.
- This is a single-user app — ratings are attributed by household member name, not authenticated accounts, and there's only one shared password for the whole app (see the deployment section if running it publicly), not per-person logins.
- `data/` (your local SQLite file, if not using `DATABASE_URL`) is gitignored and never committed. Your Gmail client secret and access token are stored as rows in the app's own database (not local files), so they persist correctly on hosts with an ephemeral filesystem, like Render's free tier.
- If deployed publicly (Section 7), set `APP_PASSWORD` (and optionally `APP_USERNAME`) as environment variables on the host — never commit them to the repo. Locally, if these aren't set, the app runs without a password prompt, same as before.
- `DATABASE_URL` (your Neon connection string, if you set one up) contains a database password — it's an environment variable on Render, never written to the repo, same treatment as `APP_PASSWORD`.
