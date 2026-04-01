# Interactive TUI

The TUI (Terminal User Interface) lets you browse, filter, search, and export app reviews in an interactive terminal interface. It is useful when you want to explore reviews visually rather than writing code or piping CLI output.

---

## Requirements

The TUI requires the `tui` extra:

```bash
pip install app-reviews[tui]
```

This installs the [Textual](https://textual.textualize.io/) library, which powers the interface.

---

## Launching the TUI

Run `fetch` without format or output flags:

```bash
app-reviews fetch
```

This starts the interactive workflow. You can also launch it by running the package directly:

```bash
python -m app_reviews
```

!!! tip
    If you pass `--format`, `--output`, or `--no-interactive`, the TUI is skipped and results go straight to the terminal or file.

---

## Walkthrough

The TUI guides you through five screens.

### Step 1: Enter App ID

Paste an app ID or a full store URL.

- For Apple App Store: a numeric ID like `123456789` or a URL like `https://apps.apple.com/us/app/example/id123456789`
- For Google Play: a package name like `com.example.app` or a URL like `https://play.google.com/store/apps/details?id=com.example.app`

### Step 2: Select Store

Choose which store to fetch from:

- **Apple App Store**
- **Google Play Store**

The TUI may auto-detect the store from the ID or URL you entered.

### Step 3: Select Countries

Pick one or more countries to fetch reviews from. The list shows 175+ countries with the most common ones at the top (US, UK, Germany, France, Japan, etc.).

Use the arrow keys to navigate and space to toggle a country on or off.

### Step 4: Set Options

Choose your fetch settings:

- **Sort order** -- newest, oldest, highest rated, or lowest rated
- **Limit** -- maximum number of reviews to fetch

### Step 5: Confirm and Fetch

The TUI shows you a summary of your selections along with the app's metadata (name, developer, category, rating). Confirm to start fetching.

A progress indicator shows the fetch status as reviews come in from each country.

### Step 6: Browse Reviews

Once fetching is complete, you land on the review browser. This is the main screen where you can:

- **Filter by rating** -- show only reviews with a specific star rating
- **Sort reviews** -- cycle through sort orders
- **Search reviews** -- full-text search across titles and bodies
- **Export reviews** -- save the current view to a file

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Toggle 1-star filter |
| `2` | Toggle 2-star filter |
| `3` | Toggle 3-star filter |
| `4` | Toggle 4-star filter |
| `5` | Toggle 5-star filter |
| `S` | Cycle sort order (newest, oldest, highest, lowest) |
| `/` | Focus the search box |
| `E` | Export the current reviews |
| `Q` | Quit the TUI |

### Filtering by Rating

Press a number key (`1` through `5`) to toggle that star rating on or off. You can combine multiple ratings -- for example, press `1` and `2` to show only 1-star and 2-star reviews.

Press the same number again to remove that filter. When no rating filters are active, all reviews are shown.

### Searching

Press `/` to focus the search box. Type your search term and press Enter. The review list updates to show only reviews where the title or body contains your search text.

Clear the search box and press Enter to show all reviews again.

### Exporting

Press `E` to export the currently displayed reviews (after any active filters and search). The TUI prompts you to choose a format and file name.
