# FormScan-Lite design system

**Idea:** friendly and multilingual, still professional. Peacock teal and marigold on a warm cream page with soft marigold, blush and lavender glows, rounded Baloo headings, and one playful element: the three-script logo (অ அ A), one letter for each supported language. Everything else stays calm.

All values live in `frontend/src/styles/tokens.css`. Components use the tokens, never raw values. Fonts are bundled with the app (`frontend/src/styles/fonts.js`, via `@fontsource`), so they work offline.

## Colour

| Token | Hex | Use |
|---|---|---|
| `--page` | `#f8f1e8` | Page background: warm cream (muted text 5.3:1) |
| `--atmosphere` | marigold / blush / lavender glows at 12–16% opacity | Decorative layer behind the page and language picker; text always sits on a white card |
| `--surface` | `#ffffff` | Cards, inputs, app bar, bottom navigation |
| `--sunken` | `#f6f1ea` | Text areas, output boxes, progress tracks |
| `--line` | `#e6dccf` | Borders (warm) |
| `--shadow-card` | soft warm shadow | Lifts cards, tab bar and picker options off the cream page |
| `--ink` / `--muted` | `#14262b` / `#55676c` | Text / secondary text (5.6:1 on white) |
| `--primary` | `#0b6e75` | Peacock teal: buttons, active tab (5.8:1 with white) |
| `--marigold` | `#f4a62a` | Warm accent: output edge, highlights, medium confidence; always with dark text |
| `--plum` | `#6b3d7a` | Third logo colour only |
| `--good` / `--warn` / `--bad` | `#2e7449` / `#8f5600` / `#b3261e` | Confidence and messages; always paired with words |

## Type

- **Headings:** Baloo 2 family: Baloo 2 (Latin), Baloo Da 2 (Bengali), Baloo Thambi 2 (Tamil), weights 600–700.
- **Body:** Hind family: Hind, Hind Siliguri (Bengali), Hind Madurai (Tamil), weights 400 and 600.
- **Scale:** 13.6 / 15.3 / 17 / 23 / 30 px. Body line height 1.6; Bengali and Tamil 1.85.

## Space and shape

Spacing in 4 px steps (`--s1` … `--s8`). Radii: cards 20 px, inputs 12 px, buttons, tabs and chips are pills. Touch targets at least 48 px.

## Layout

- **Phones (≤ 640 px):** compact app bar (status shown as a dot), full-width content, tabs as a bottom navigation bar with rounded top corners, full-width primary buttons.
- **Larger screens:** a single 720 px column; tabs are a pill switcher under the app bar.

## Rules

- The logo is the only decorative element; don't add others.
- Every status says its meaning in words ("Check a few words"), not just colour.
- Keyboard focus is always visible (marigold ring). Motion respects `prefers-reduced-motion`.
