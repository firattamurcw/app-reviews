# Interactive TUI

The TUI (Terminal User Interface) lets you browse, filter, search, and export app reviews interactively.

---

## Requirements

```bash
pip install app-reviews[tui]
```

Or with uv:

```bash
uv add "app-reviews[tui]"
```

---

## Launching the TUI

```bash
app-reviews
```

---

## Walkthrough

The TUI guides you through five screens.

### Step 1: Enter App ID

Paste an app ID or a full store URL:

- **Apple App Store:** numeric ID like `123456789` or a full URL
- **Google Play:** package name like `com.example.app` or a full URL

### Step 2: Select Store

Choose **Apple App Store** or **Google Play Store**. The TUI may auto-detect from the ID format.

### Step 3: Select Countries

Pick one or more countries. Common ones are listed first. Use arrow keys to navigate and space to toggle.

### Step 4: Set Options

- **Sort order** -- newest, oldest, highest rated, or lowest rated
- **Limit** -- maximum number of reviews

### Step 5: Confirm and Fetch

Review your selections and app metadata. Confirm to start fetching. A progress indicator shows fetch status.

### Step 6: Browse Reviews

The review browser lets you:

- **Filter by rating** -- show only specific star ratings
- **Sort reviews** -- cycle through sort orders
- **Search reviews** -- full-text search across titles and bodies
- **Export reviews** -- save to a file

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1`-`5` | Toggle star rating filter |
| `S` | Cycle sort order |
| `/` | Focus search box |
| `E` | Export current reviews |
| `Q` | Quit |
