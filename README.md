Curio — A Content Recommendation Engine

A Python-based blog recommendation system with a custom classification pipeline, collaborative filtering, and a feedback-driven interest model — built entirely from scratch without any third-party ML libraries.

Overview
Curio is a terminal-based reading platform that learns what you like by watching how you engage with content. The core challenge it solves: keeping a recommendation feed diverse without becoming a content bubble. Most recommendation systems over-optimize for engagement, locking users into an increasingly narrow set of topics. Curio is designed to resist that pattern.

The system is built on three layers: a content classifier that routes raw text into typed niches, a scoring engine that tracks per-user interest over time, and a peer discovery layer that surfaces content from users with overlapping taste profiles.

Architecture

curio/
├── main.py           # Entry point — dashboard, reading loop, session management
├── Engine.py         # Recommendation logic, interest scoring, peer map
├── Connector.py      # Database abstraction layer (credentials via .env)
├── Verification.py   # Sign-up, sign-in, password recovery, interest seeding
├── Settings.py       # Account management — username, password, saves, deletion
├── uploader.py       # Blog classifier — scores new content and routes to a niche
├── file_transfer.py  # Batch ingestion pipeline — validates and vaults content
├── scanner.py        # Niche discovery — detects new topic clusters from raw text
├── signals.json      # Master keyword dictionary keyed by niche, with influence weights
├── meta.json         # Upload counters per niche (used for file naming)
└── stats.json        # Persistent reject ID tracker
```


Vault/          ← Verified and stored blog files (.txt)
Noise/          ← Rejected or unclassified content
Automotive/     ← Niche staging folders (one per genre)
Finance/
Nature/
... etc.
```

---
Key Features

## 80/20 Feed Logic
The primary feed pulls **80% of recommendations** from a user's highest-scoring niches and routes the remaining **20% toward genres they have not yet rated negatively**. This is implemented in `Engine.get_recommended_blog_v2()` and runs on every feed request. The split is intentional: pure interest-matching leads to filter bubbles; pure randomness breaks trust. The 80/20 ratio keeps the feed familiar while continuously expanding the user's exposure surface.

### Interest Scoring Model
Each user maintains a per-niche point balance stored in `user_interests`. Points accumulate through engagement and decay over time when the user is inactive:

| Action | Points |
|---|---|
| Like (in discovery mode) | +15 |
| Save (treated as a super-like) | +15 (like) + counted toward saves |
| Dislike (in discovery mode) | −10 |
| Session boost on logout | ×1.1 per active genre |
| Daily decay (on sign-in) | ×0.99 per day since last session |

The decay function (`apply_decay` in `Verification.py`) prevents stale interests from dominating the model indefinitely. A user who stops engaging with Finance content will gradually see it deprioritized, without any explicit opt-out.

### Keyword Classifier
New content is classified by scoring its title and body against `signals.json` — a manually curated dictionary of niche-specific keywords, each assigned an influence weight (1–3). Fuzzy matching via Python's `difflib` catches near-matches (e.g. *"fermentation"* matching *"fermented"*), making the classifier resilient to natural language variation.

Classification is a two-pass process:
1. **Title scoring** determines the candidate niche (with tie-breaking logic for ambiguous titles).
2. **Density check** validates that the body content is substantive and on-topic — the keyword density must fall between 1% and 30%. Content outside this range is routed to `Noise/`.

### Collaborative Filtering (Peer Map)
On each sign-in, `update_peer_connections()` queries for users who share at least **3 top-3 genres** with the current user (filtered to niches with more than 50 points). Matching users are written into a `collaborative_map` table with a similarity score equal to the number of overlapping niches.

The discovery feed can then pull from a peer's liked content — surfacing blogs the current user has never seen, sourced from someone with proven taste overlap.

### Content Health & Ghosting
A background check (`check_blog_health`) runs against each blog after interaction. The health score is calculated as:

```
health_score = (total_likes × 2) − (total_dislikes × 5)
```

If a blog scores below −50, its status is set to `'ghosted'` and it stops appearing in any feed. Dislikes are penalized at 2.5× the rate of likes to surface low-quality content quickly.

### Niche Discovery (`scanner.py`)
The scanner analyzes the `Noise/` folder to detect emergent topic clusters in rejected content. It builds a co-occurrence map across files, identifies words that appear together frequently, prunes low-signal terms, and proposes a new niche title (formatted as `"Word1 & Word2"` using the two highest-influence signature words). If confirmed, the niche is written into `signals.json`, `meta.json`, and a new folder is created — with all matching files migrated automatically.

---

## Security

- **No credentials in source.** All database connection details are loaded from a `.env` file at runtime using `python-dotenv`. The `.env` file is excluded from version control.
- **Passwords are hashed with bcrypt** (work factor via `bcrypt.gensalt()`). Plain-text passwords are never stored or logged.
- **Recovery answers are SHA-256 hashed** (lowercased and stripped before hashing to prevent case/whitespace collisions).
- **ID generation** uses `secrets.choice()` (cryptographically random) for user and history IDs. File IDs in the ingestion pipeline use `random.choices()` (non-sensitive, collision-retried).
- **Git history** was hard-reset to permanently remove a previously committed credential. The working history begins from a clean state.

---

## Setup

**Prerequisites:** Python 3.9+, MySQL 8+

```bash
# 1. Clone the repo
git clone https://github.com/your-username/curio.git
cd curio

# 2. Install dependencies
pip install mysql-connector-python python-dotenv bcrypt

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. Set up the database schema
# Run the provided schema.sql against your MySQL instance

# 5. Create required directories
mkdir -p Vault Noise Automotive Finance Nature Food Fitness Space

# 6. Run
python main.py
```

**Environment variables required (`.env`):**
```
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=classifier
```

---

## Database Schema

To replicate this project, create a MySQL database named `classifier` and build the following tables. The schema is designed so that every component of the recommendation engine has a dedicated, purpose-built table — nothing is overloaded.

---

### `users` — Core Profiles

Manages identity and account lifecycle. The `status` enum allows soft-deletion: a deleted account nulls out the username (freeing it for reuse) without purging interaction history, keeping the recommendation data intact.

| Column | Type | Notes |
|---|---|---|
| `user_id` | `VARCHAR(7)` | Primary key. Generated via `secrets.choice()`. |
| `username` | `VARCHAR(50)` | Unique. Used for login. Set to `NULL` on deletion. |
| `display_name` | `VARCHAR(100)` | Public-facing name shown in the UI. |
| `password_hash` | `TEXT` | bcrypt hash. Plain-text password is never stored. |
| `status` | `ENUM('active', 'deleted')` | Controls login eligibility. |

---

### `ranker` — The Content Library

The central table the Engine queries to serve blogs. Every blog file ingested through `file_transfer.py` gets a row here. The engagement columns (`likes`, `dislikes`, `views`, `saves`) are updated in real time and feed directly into the health score and ranking logic.

| Column | Type | Notes |
|---|---|---|
| `id` | `VARCHAR(11)` | Primary key. 11-character alphanumeric ID generated at ingest time. |
| `filepath` | `TEXT` | Absolute path to the `.txt` file in `Vault/`. |
| `genre` | `VARCHAR(100)` | The niche this blog was classified into. |
| `points` | `INT` | General ranking score (reserved for future weighting). |
| `views` | `INT` | Incremented every time a user opens the blog. |
| `likes` | `INT` | Total likes across all users. |
| `dislikes` | `INT` | Total dislikes. Weighted at 2.5× in the health formula. |
| `saves` | `INT` | Total saves. A save also increments `likes`. |
| `status` | `VARCHAR(20)` | `'Active'` or `'ghosted'`. Ghosted blogs are excluded from all feeds. |
| `upload_date` | `DATETIME` | Timestamp of ingest. Used for recency-based fallback queries. |

---

### `user_interests` — The Preference Map

This is the core data structure the 80/20 algorithm reads from. Every user gets one row per niche, seeded at 50 points on account creation. Points rise and fall with engagement and decay passively over time.

| Column | Type | Notes |
|---|---|---|
| `interest_id` | `VARCHAR(7)` | Primary key. |
| `user_id` | `VARCHAR(7)` | Foreign key → `users.user_id`. |
| `genre` | `VARCHAR(100)` | The niche being tracked (matches `ranker.genre`). |
| `points` | `DECIMAL(10, 5)` | Decimal precision required for the `×0.99` daily decay multiplier. |
| `last_updated` | `DATETIME` | Timestamp used by `apply_decay()` to calculate days elapsed since last session. |

---

### `user_history` — The Interaction Log

Every blog a user encounters is logged here. The Engine uses this table to ensure the same blog is never shown twice (via `LEFT JOIN ... WHERE h.blog_id IS NULL`). The boolean flags capture the nature of each interaction.

| Column | Type | Notes |
|---|---|---|
| `history_id` | `VARCHAR(7)` | Primary key. |
| `user_id` | `VARCHAR(7)` | Foreign key → `users.user_id`. |
| `blog_id` | `VARCHAR(11)` | Foreign key → `ranker.id`. |
| `is_liked` | `TINYINT(1)` | `1` if liked, `0` otherwise. Also set to `1` on save. |
| `is_disliked` | `TINYINT(1)` | `1` if disliked, `0` otherwise. |
| `is_saved` | `TINYINT(1)` | `1` if saved to the user's library. |
| `interacted_at` | `DATETIME` | Timestamp of the interaction. Updated on repeat visits via `ON DUPLICATE KEY UPDATE`. |

---

### `collaborative_map` — The Peer Index

Populated on every sign-in by `update_peer_connections()`. Stores directional user-to-peer relationships. The `similarity_score` is the raw count of overlapping top-3 genres (max value: 3). Used by the "People Like You" discovery feed to source content recommendations.

| Column | Type | Notes |
|---|---|---|
| `user_id` | `VARCHAR(7)` | The current user. Composite primary key with `peer_id`. |
| `peer_id` | `VARCHAR(7)` | The matched peer. Foreign key → `users.user_id`. |
| `similarity_score` | `INT` | Number of shared top-3 genres (1–3). Higher = stronger match. |

---

### `user_feedback` — Exit Surveys

Populated when a user deletes their account. Captures lightweight NPS-style data to track app health over time without tying feedback to a recoverable identity.

| Column | Type | Notes |
|---|---|---|
| `feedback_id` | `INT` | Auto-increment primary key. |
| `recommend_score` | `INT` | "How likely to recommend?" (1–10 scale). |
| `return_score` | `INT` | "Will you return?" (1–10 scale). |
| `exit_reason` | `TEXT` | Optional free-text reason for leaving. |
| `submitted_at` | `DATETIME` | Timestamp of deletion/submission. |

---

### `safety` — Account Recovery

Stores one optional recovery question per user. The answer is hashed with SHA-256 (lowercased and whitespace-stripped before hashing) so even a database breach cannot reveal the answer in plain text.

| Column | Type | Notes |
|---|---|---|
| `user_id` | `VARCHAR(7)` | Primary key. One recovery record per user. Foreign key → `users.user_id`. |
| `question_text` | `TEXT` | The security question set by the user. Stored as plain text. |
| `answer_hash` | `VARCHAR(64)` | SHA-256 hex digest of the lowercased, stripped answer. |

---

## Roadmap

- [ ] Web interface (Flask or FastAPI) to replace the terminal loop
- [ ] Admin dashboard for niche management and content health monitoring
- [ ] Weighted decay curve (configurable per-niche half-life)
- [ ] Export user interest profile as JSON
- [ ] Unit test suite for classifier scoring and density validation

---
