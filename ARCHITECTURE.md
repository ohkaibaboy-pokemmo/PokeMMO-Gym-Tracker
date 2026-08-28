# Architecture and compliance boundary

PokeMMO Gym Tracker is an unofficial standalone community companion. It is not affiliated with or endorsed by PokeMMO.

## Data flow

The intended data flow is one-way:

`PokeMMO -> locally written chat_*.log -> Gym Tracker -> local state/UI`

The tracker does not send information, commands, keyboard/mouse/controller input, or network requests back to the PokeMMO client or servers.

The earnings feature stays inside the same boundary. It consumes the vanilla battle-log payout line that PokeMMO already wrote to disk and combines it with local route/payout data and user-entered charm prices.

UI scaling is entirely local presentation state and has no interaction with the PokeMMO process/client.

## Runtime modules

- `app/main.pyw` — minimal application entry point and installation order for the presentation controllers.
- `app/tracker/constants.py` — app version, gym data, verified rematch trainers, display modes, and built-in route data.
- `app/tracker/core.py` — normalization and gym/leader helper functions.
- `app/tracker/engine.py` — vanilla chat-log parsing, confirmed-victory processing, cooldown/five-battle processing, and short-lived victory context used to link payout lines.
- `app/tracker/earnings.py` — local base payout table, payout-event persistence helpers, current-run accounting, and charm/Donator projection formulas.
- `app/tracker/earnings_ui.py` — Full-view earnings summary strip and offline calculator window.
- `app/tracker/logs.py` — passive `chat_*.log` discovery and incremental tailing.
- `app/tracker/state.py` — local JSON persistence and migration from prototype versions.
- `app/tracker/trainers.py` — verified-rematch catalogue, repeat-evidence learning, and five-battle recalculation.
- `app/tracker/themes.py` — UI theme values.
- `app/tracker/presentation.py` — Full-view dashboard/table presentation.
- `app/tracker/compact_ui.py` — aligned frameless always-on-top Compact view and responsive compact table sizing.
- `app/tracker/scaling.py` — explicit persistent UI-scale controller; scales app-owned fonts/styles/dimensions without changing Tk's global DPI setting.
- `app/tracker/leader_art.py` / `leader_art_integration.py` — original locally generated Gym Leader portraits, optional local PNG overrides, and portrait scaling.
- `app/tracker/ui.py` — base Tkinter application, Full view, route editor, state/filter actions, and manual correction controls.

The current runtime does not import any of the old incremental prototype modules.

## What the application reads

The application reads ordinary text files selected from the user's PokeMMO log directory. The live watcher deliberately accepts filenames matching `chat*.log` and ignores `console.log` and unrelated logs. During parsing, only `Battle` and `System Messages` lines are acted on.

Relevant vanilla battle events include challenge, player send-out, confirmed victory, and prize-money lines such as `<character> got $<amount> for winning!`.

Vanilla PokeMMO log strings are the canonical supported format. Third-party string mods may work where their output remains compatible, but are not part of the guaranteed parser contract.

## Earnings/payout linking

A payout is never inferred from its numeric value. The engine retains a short-lived context for the most recent confirmed victory, including timestamp, player, and opponent. A subsequent payout line is stored only when it can be linked to that confirmed victory for the same character within the small matching window.

Payout events are de-duplicated, so replaying the same log does not double-count earnings. Replay can also backfill prize money for a victory that was already in the old cooldown state before the earnings feature existed.

Each character keeps a local `run_started_at` timestamp. The first detected payout starts a run automatically if no accounting window exists; the user can explicitly reset the run timestamp without deleting historical payout events.

## Local projection data

Gym base payouts are embedded locally for route projections. Manual charm prices are stored in local state. Donator/charm projections are calculated locally. The application does not fetch GTL prices or query a market-price service.

Actual detected payouts are kept separate from projections and are treated as the authoritative amount actually awarded by PokeMMO for that battle.

## UI scaling

The user-selected scale is stored locally as `ui_scale` with supported values from `0.85×` through `2.0×`.

The implementation deliberately does **not** call Tk's global/process-wide `tk scaling` command. Instead it scales only application-owned presentation:

- Tk widget fonts captured from their baseline configuration;
- ttk button/checkbutton/combobox/table styles;
- Full-view table rows and columns;
- original/local leader portrait display size;
- Compact geometry, padding, table widths, rows, and custom title-bar controls;
- secondary-window font sizes/minimum dimensions.

Normal Full-view windows resize proportionally on a scale change while respecting screen bounds. Maximized windows remain maximized. Compact geometry is reset to a proportionate default on a scale change while retaining the saved screen position, after which user resizing is remembered normally.

## What the application does not do

The tracker does not inject code, hook functions, read process memory, inspect packets, connect to PokeMMO servers, modify game/client files, capture the screen, use OCR, scan the PokeMMO process, or automate player inputs.

The application has **no runtime dependency on a market-data API or other external service**.

## Local state

State is stored under the user's local application-data directory in `PokeMMOGymCooldownTracker/state.json`. It contains tracker-derived timestamps, characters, route/view preferences, custom routes, learned rematch trainers, earnings settings, de-duplicated payout events, current earnings-run start timestamps, UI scale, and window/Compact geometry. PokeMMO chat logs are not copied into application state.

## Regression testing

`tests/test_parser.py` contains sanitized vanilla-format parser tests based on observed PokeMMO log structure, including payout linking/replay behaviour. `tests/test_earnings.py` covers route totals, charm/Donator projections, run summaries, resets, and currency formatting. `tests/test_scaling.py` covers the supported scale labels, normalization and deterministic integer pixel scaling. Test data uses fictional character names and does not include private user chat logs.

GitHub Actions syntax-checks the clean runtime modules, runs the regression suite, and builds the same `app/main.pyw` entry point used for the Windows executable.
