# Insighta Labs — Intelligence Query Engine

A Django REST API that stores demographic profile data and exposes it through advanced filtering, sorting, pagination, and a rule-based natural language query interface.

---

## Stack

- Python 3.13 / Django 6 / Django REST Framework
- SQLite (local) / Gunicorn (production)
- No external AI or LLM services

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_profiles seed_profiles.json

python manage.py runserver
```

---

## Endpoints

### `GET /api/profiles`

Returns a paginated, filterable, sortable list of profiles.

**Filter parameters**

| Parameter | Type | Description |
|---|---|---|
| `gender` | string | `male` or `female` |
| `age_group` | string | `child`, `teenager`, `adult`, `senior` |
| `country_id` | string | ISO 3166-1 alpha-2 code (e.g. `NG`, `KE`) |
| `min_age` | integer | Inclusive lower age bound |
| `max_age` | integer | Inclusive upper age bound |
| `min_gender_probability` | float | Minimum gender confidence (0.0–1.0) |
| `min_country_probability` | float | Minimum country confidence (0.0–1.0) |

**Sort parameters**

| Parameter | Values | Default |
|---|---|---|
| `sort_by` | `age`, `created_at`, `gender_probability` | `created_at` desc |
| `order` | `asc`, `desc` | `asc` |

**Pagination parameters**

| Parameter | Default | Max |
|---|---|---|
| `page` | `1` | — |
| `limit` | `10` | `50` |

**Example**

```
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```

**Response**

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 43,
  "data": [ ... ]
}
```

---

### `GET /api/profiles/search?q=<query>`

Accepts a plain-English query string and converts it into database filters using rule-based parsing. No AI or LLMs are involved. Pagination (`page`, `limit`) applies here too.

**Example queries**

```
GET /api/profiles/search?q=young males from nigeria
GET /api/profiles/search?q=females above 30
GET /api/profiles/search?q=adult males from kenya
GET /api/profiles/search?q=male and female teenagers above 17
GET /api/profiles/search?q=elderly people from ghana
```

**Success response** — same shape as `/api/profiles`

**Failure response** — when the query yields no recognisable filters:

```json
{ "status": "error", "message": "Unable to interpret query" }
```

---

### `GET /api/profiles/<uuid>`

Returns a single profile by its UUID v7 primary key.

### `POST /api/profiles`

Creates a profile by calling the Genderize / Agify / Nationalize external APIs. Body: `{ "name": "..." }`.

### `DELETE /api/profiles/<uuid>`

Deletes a profile.

---

## Natural Language Parsing

The search endpoint converts free-form English into structured database filters using sequential regex pattern matching. The parser runs three independent passes — gender, age, country — and combines whatever each pass finds into a single `AND` query. No parse tree, no NLP library, no AI.

### How it works

1. The query string is lowercased and stripped.
2. Each dimension (gender, age, country) is matched independently using `re.search`.
3. Any dimension that produces no match is simply omitted from the filter — it does not restrict results.
4. If **no** dimension matches at all, the parser returns `None` and the endpoint responds with `"Unable to interpret query"`.

### Supported keywords and their mappings

#### Gender

| Query contains | Maps to |
|---|---|
| `male` / `males` (without `female`) | `gender = male` |
| `female` / `females` (without `male`) | `gender = female` |
| `male and female` / both words present | no gender filter (all genders returned) |

Gender is detected with whole-word matching (`\bmale\b`) so "female" does not accidentally trigger the male branch.

#### Age groups

These keywords set a stored `age_group` filter or a numeric age range:

| Query contains | Maps to |
|---|---|
| `young` | `min_age = 16`, `max_age = 24` (range, not a stored group) |
| `teenager` / `teenagers` | `age_group = teenager` |
| `child` / `children` / `kid` / `kids` | `age_group = child` |
| `senior` / `seniors` / `elderly` / `old people` | `age_group = senior` |
| `adult` / `adults` | `age_group = adult` |

Age group keywords are checked in priority order: `young` first, then the stored groups. Only the first match is used.

#### Explicit age bounds

These phrases extract a number from the query and set a numeric bound:

| Pattern | Example | Maps to |
|---|---|---|
| `above N` / `over N` / `older than N` | `above 30` | `min_age = 30` |
| `below N` / `under N` / `younger than N` | `below 18` | `max_age = 18` |

Age bounds can stack on top of age group keywords. `teenagers above 17` produces `age_group = teenager` **and** `min_age = 17`.

#### Country

The parser looks for the pattern `from <country name>` or `in <country name>` and maps the country name to an ISO 3166-1 alpha-2 code.

| Query contains | Maps to |
|---|---|
| `from nigeria` | `country_id = NG` |
| `from south africa` | `country_id = ZA` |
| `in kenya` | `country_id = KE` |
| `from the uk` / `from britain` | `country_id = GB` |
| `from the usa` / `from america` | `country_id = US` |

The country lookup performs an exact match first, then a substring fallback for multi-word names. Abbreviations like `uae`, `uk`, `usa`, `drc` are in the lookup table.

### Worked examples

| Query | Parsed filters |
|---|---|
| `young males` | `gender=male`, `min_age=16`, `max_age=24` |
| `females above 30` | `gender=female`, `min_age=30` |
| `people from angola` | `country_id=AO` |
| `adult males from kenya` | `gender=male`, `age_group=adult`, `country_id=KE` |
| `male and female teenagers above 17` | `age_group=teenager`, `min_age=17` |
| `elderly women from ghana` | `gender=female`, `age_group=senior`, `country_id=GH` |

---

## Limitations

### Parser limitations

**No negation.** Phrases like "not from nigeria" or "males excluding seniors" are not handled. The word "not" is silently ignored and the positive term may still match.

**Single country only.** "people from nigeria or kenya" is not supported. The parser captures only the first `from`/`in` phrase it finds.

**"Young" overrides age groups.** If the query contains both `young` and `teenager`, the `young` branch fires first and sets a numeric range (`16–24`). The `teenager` age_group filter is never set. The two are mutually exclusive by design.

**Age bounds don't compose with "young".** A query like "young males above 20" will set `min_age=16`, `max_age=24` from "young", and then overwrite `min_age` with `20` from "above 20" — resulting in `min_age=20`, `max_age=24`. This is technically correct but may surprise users expecting the "young" range to be preserved exactly.

**Adjectives like "old" are mapped to senior.** The word "old" inside a phrase like "old people" maps to `age_group=senior`. Standalone "old males" also matches this because the regex `\bold people\b` does not match, but `\belderly\b` and `\bseniors?\b` also don't — so "old males" alone does not produce an age filter. Only "old people" triggers senior.

**No ordinal or relative language.** Phrases like "the youngest 10", "most common country", "top earners", or "recently added" are not supported.

**Country disambiguation is first-match.** The substring fallback for country names picks the first entry in the dictionary whose name is a substring of the query text (or vice versa). Dictionary iteration order is insertion order (Python 3.7+), so for an ambiguous substring the result is deterministic but may not be what the user intended. For example, "guinea" will match `Guinea (GN)` before `Guinea-Bissau (GW)` or `Equatorial Guinea`.

**No spelling correction.** "Nigria", "Kenay", "Tanznia" return no country match and the country filter is dropped silently rather than raising an error.

**Purely additive logic.** All parsed filters are combined with `AND`. There is no way to express `OR` across dimensions (e.g. "males from nigeria or ghana").

**No name search.** The natural language endpoint cannot search by a person's name.

### Structural limitations

**SQLite in local mode.** The seeded 2026-record dataset fits comfortably in SQLite, but for a production deployment a Postgres database is recommended for concurrency and full-text index support.

**Single-country NL filter only.** The structured `/api/profiles` endpoint supports only one `country_id` value per request for the same reason — there is no multi-value filter syntax.

**`min_gender_probability` and `min_country_probability` are not exposed through the NL parser.** They are only available as explicit query parameters on `/api/profiles`.
