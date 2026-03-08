# Copilot Instructions for MyVocTrainer

## Project Overview
MyVocTrainer is a tkinter-based vocabulary trainer for French-German language learning. It implements an intelligent spaced-repetition system that prioritizes weak items and those not recently reviewed.

## Architecture & Data Flow

**Single-file monolithic app** (`main.py`) with:
- **Data layer**: Global pandas DataFrame loaded from `phrases.xlsx` at module startup
- **UI layer**: tkinter views managed by the `App` class with two main screens

### Key Data Structure
The Excel file contains vocabulary items with these columns:
- `fr`, `de`: French/German translations (user selects direction)
- `themes`: Category filter
- `score`: Numeric metric (higher = stronger knowledge, 0 = new)
- `last_review`: Datetime of most recent review (drives recency penalty)

### Quiz Session Algorithm
1. User selects theme, number of phrases (10/20/50), direction (FR→DE or DE→FR)
2. **Weighted sampling** in `start()` method:
   - Score weight: `1/(score+1)` → items with low scores get high weight
   - Recency weight: `(days since review / 30)` → old items get boosted
   - Combined: `weight = score_term + recency_term`
   - Handles edge case: if all weights = 0, uniform distribution
3. Phrase list shuffled via `sample(weights=...)` respects calculated weights
4. Quiz loop: show question → reveal answer → mark correct/wrong → auto-advance
5. **Error handling**: Wrong answers appended to `errors` list, repeated as second pass after main session
6. Session ends with xlsx persistence: `df.to_excel(FILE, index=False)`

## Critical Developer Workflows

### Running the App
```bash
python main.py
```
Requires: `tkinter` (stdlib), `pandas`, `openpyxl` (for Excel I/O)

### Data Flow & Persistence
- Data loaded once at module import (line 8-9)
- All modifications update the global `df` object in-memory
- Persistence happens on two events: session exit (`return_to_menu`) AND session complete (`load_question` when index >= session length)
- **Important**: Direct cell assignment `df.at[row_id, col] = value` is used, not `.loc[]` or `.iloc[]`

## Project-Specific Patterns & Conventions

### UI State Management
- **Screen switching via widget destruction**: `widget.destroy()` clears frame, then `setup_quiz()` or `setup_menu()` rebuilds
- Menu state: theme, direction, count stored in `tk.StringVar` and `tk.IntVar` bound to comboboxes
- Quiz state: `self.index`, `self.session` (list of selected row indices), `self.errors` (failed indices)

### Naming Conventions
- French UI labels (`"Afficher réponse"`, `"Quitter session"`) - maintain this localization
- Variable names: snake_case for Python (`last_review`, `nb_var`), camelCase for tkinter vars (`theme_var`)
- French terminology: "themes" = categories, "score" = knowledge strength metric

### Error Handling
- Pandas `.fillna()` used liberally to guard against missing values:
  - `last_review` defaults to `2000-01-01` when null
  - `score` defaults to 0 when null
  - `errors='coerce'` on datetime parsing to avoid crashes
- No try-except blocks; relies on defensive data prep

## Integration Points & Dependencies

| Dependency | Purpose | Version/Notes |
|-----------|---------|---------------|
| `tkinter` | GUI framework | Stdlib, uses ttk for modern widgets |
| `pandas` | Data manipulation | `read_excel()`, datetime handling, weighted sampling |
| `openpyxl` | Excel backend | Implicit pandas dependency |

## Common Modification Patterns

**Adding a new quiz feature**: Modify `setup_quiz()` layout (add labels/buttons), then update corresponding handler method (e.g., add method called by button `command=`).

**Changing scoring logic**: Edit the weight calculation in `start()` method (lines 50-56). Keep formula structure: `score_term + recency_term`.

**Adding phrase metadata**: Add column to xlsx, ensure `fillna()` guard in `start()` method when parsing, then reference in UI via `row[col_name]`.

**Session replay mode**: Errors list already re-creates session after main quiz—this is intentional spaced-repetition pattern. Preserve logic in `load_question()` lines 100-103.
