# PokeMMO Gym Tracker — v0.6 Dashboard UI Specification

**Status:** Adopted design direction / implementation specification  
**Stable fallback:** `v0.5.5`  
**Scope:** Presentation architecture only. Existing tracking, cooldown, route, earnings and log behaviour must remain intact.

## 1. Goal

Replace the current utility-style Full view with a cohesive dashboard interface based on the approved concept direction, while preserving the existing tracker engine and data model.

The new UI should feel like a polished PokeMMO companion rather than a spreadsheet or generic Tkinter utility. It must remain practical during real reruns, scale cleanly on Windows, and keep the current passive/log-only compliance boundary unchanged.

The redesign has two related views:

- **Full dashboard** — information-rich, visually polished, intended for setup, review and general use.
- **Compact mini-dashboard** — visually related, but deliberately simple and optimized to sit over PokeMMO during a rerun.

The design target is the pair of dashboard concepts approved in the project conversation on 2026-08-24. The concepts are guidance, not a pixel-perfect contract; implementation must prioritize readability, scaling and reliable live updates.

## 2. Non-negotiable behaviour to preserve

The v0.6 UI must not rewrite or weaken validated tracker behaviour.

Preserve:

- live `chat_*.log` watching and historical replay;
- confirmed Gym Leader win detection;
- 18-hour cooldown tracking;
- separate 5-other-trainer rule;
- conservative rematch-trainer catalogue and repeat-evidence learning;
- per-character state;
- region filtering;
- built-in and custom routes;
- route order / route progress / next-route highlighting;
- manual Mark Defeated / Mark Ready / Forget controls;
- earnings capture, current-run reset and offline calculator;
- Dark / Light / PokeMMO themes;
- `0.85×` through `2.0×` explicit UI scaling;
- Compact always-on-top behaviour and remembered geometry;
- fresh app launch opening Full view;
- local leader portrait overrides;
- no runtime external API calls.

The tracker engine remains the source of truth. Dashboard components consume existing state/events; they do not duplicate cooldown or earnings logic.

## 3. Design principles

### 3.1 Subtle dashboard, not flashy gaming UI

Use restrained visual hierarchy:

- charcoal/slate surfaces in Dark;
- thin borders and modest corner treatment;
- limited glow;
- muted gold/olive route-next selection;
- soft green for READY;
- amber for WAITING;
- cool blue for COOLDOWN;
- subdued purple/grey for UNKNOWN;
- money accent inspired by the in-game display without making the whole UI gold/orange.

Avoid oversized logos, decorative shields, strong gradients or large branding blocks.

### 3.2 Layout is independent of theme

Dark, Light and PokeMMO use the **same dashboard structure**. Theme changes colours/surfaces/typography treatment only; widgets must not move when theme changes.

### 3.3 Theme is independent of background skin

Prepare the architecture for a future optional background layer:

- `Plain` initially;
- future original `Night Sky`;
- future original/map-inspired background;
- possible user-local custom background.

A background is a decorative skin behind readable dashboard surfaces, not a separate layout or theme.

Do not bundle copied official route-map art solely to provide a background. Prefer original/map-inspired artwork or local user overrides.

### 3.4 Full and Compact are related, not identical

Full view is the complete dashboard. Compact is a mini-dashboard for rerun execution and should not become a tiny copy of every Full-view feature.

## 4. Full dashboard target

### 4.1 Header / app state

Top bar should include:

- understated app mark or simple icon;
- `Gym Rerun Tracker` title;
- live-log indicator on the right using `status_var`;
- standard Windows window controls remain native in Full view.

No large decorative logo.

### 4.2 Status + earnings dashboard row

The first major content row contains five dashboard areas:

1. **Ready** — count, green accent.
2. **Waiting** — count, amber accent.
3. **Cooldown** — count, blue accent.
4. **Unknown** — count, muted purple/grey accent.
5. **Run Earnings** — larger card using the existing earnings controller.

Run Earnings should display:

- primary **Actual run** value prominently;
- Route base;
- Route gyms progress;
- Other payouts;
- optional tiny decorative sparkline only if implemented locally from run history; do not introduce network/data dependencies just to draw a graph.

### 4.3 In-game-style money presentation

The approved concept replaces the generic yen presentation with a PokeMMO-style money presentation.

UI rules:

- use `$` formatting in the tracker UI rather than `¥`;
- show a small stacked-coin / money icon beside the primary run-earnings total;
- use the same currency convention consistently in Full table payout, Detector payout text and calculator UI;
- calculations and integer values are unchanged — this is presentation only.

Asset rule:

- prefer a small original pixel-art recreation of the stacked-coin visual generated/drawn by the app rather than bundling a ripped game sprite;
- the visual can closely follow the familiar in-game concept (stacked coins + money marker) but must remain a project-owned implementation asset.

### 4.4 Controls card

Below the status/earnings row, use one framed controls card.

Primary fields:

- Character;
- Region;
- Route / order;
- Display;
- UI Scale;
- Theme.

Actions grouped to the right or in a secondary area:

- Replay Log File;
- Choose Log Folder;
- Compact View;
- Calculator;
- Reset Run;
- Manage Routes adjacent to Route / order.

Controls must remain keyboard-accessible and use the existing variables/callbacks.

### 4.5 Gym list card

Replace the Full-view Treeview presentation with a purpose-built dashboard list.

Visible columns:

1. Portrait
2. `#`
3. Leader
4. Gym
5. Region
6. 5-rule
7. Cooldown
8. Last Defeated
9. Status
10. Payout

#### Persistent row architecture

Do not destroy and recreate every row on the one-second timer.

Implement a `DashboardGymList` containing reusable/persistent `GymRow` components. Rebuild row membership/order only when filters/route/character/display options materially change. Live ticks update label values and colours in place.

This reduces flicker and allows richer styling without excessive widget churn.

#### Row visual rules

- approximately 40–48px portrait at `1.0×`;
- quiet row separators;
- subtle hover/selection treatment;
- next route target receives a restrained olive/gold edge/background, not a bright full-width glow;
- status uses compact pill/badge styling;
- timer colours follow status but remain readable in all three themes;
- `Need N battle(s)` remains the actionable expired-cooldown wording;
- ready timer remains `00:00:00`;
- unknown values remain `—` where appropriate.

#### Row selection / manual correction

Clicking a row must select the same logical gym used by existing manual correction controls. Existing Mark Defeated / Mark Ready / Forget behaviour must remain accessible, either as a small footer/action bar or a selected-row action area.

### 4.6 Leader portraits

The dashboard should make leader portraits a genuine visual feature.

Default asset path:

- evolve current original `leader_art.py` portraits from 36px to a dashboard-friendly logical portrait size around 44–48px at `1.0×`;
- retain leader-specific palettes/accessory cues;
- do not copy official game sprite pixels for the default distributed assets.

Local override path remains:

`%LOCALAPPDATA%\PokeMMOGymCooldownTracker\leader_sprites\`

Overrides should be fitted/cropped into the dashboard portrait slot without distorting aspect ratio.

The portrait loader should be shared by Full and any future portrait-bearing views.

### 4.7 Detector card

Detector becomes a first-class dashboard panel below the gym list rather than a generic appended text box.

Target behaviour:

- visible panel title and live indicator;
- recent events displayed as compact rows;
- event type badge/icon such as INFO / PAY / BATTLE;
- preserve chronological event content currently emitted by the engine;
- optional Clear button;
- retain enough history to be useful without growing indefinitely.

Responsive rule:

- Detector must never become effectively unreachable because the window is slightly too short;
- central gym list should give up height first;
- optionally add a collapse/expand control if needed after Windows testing.

## 5. Compact mini-dashboard target

Compact remains frameless, always-on-top and geometry-persistent.

### 5.1 Header

- `Gym Tracker`;
- live-log indicator;
- existing restore/full control and close control at far right;
- same subtle dashboard border/surface language as Full view.

### 5.2 Filters

Keep the accepted two-row structure:

- Character | Region
- Route | Display

No Theme or UI Scale control in Compact.

### 5.3 Mini status strip

Replace the plain progress sentence with segmented mini-dashboard metrics:

- Ready `x/route`;
- Waiting;
- Cooldown;
- Unknown;
- one compact **Actual run money** value at the right when space allows, using the same coin icon + `$` convention.

If width becomes too constrained at smaller scale/window sizes, money is the first status item allowed to hide; core rerun status must remain visible.

### 5.4 Compact gym list

Keep only:

- `#`
- Gym
- Cooldown
- 5-rule

Do not add portraits, Leader, payouts, Detector, earnings breakdown, calculator or manual actions to Compact.

Use subtle dashboard row styling and next-route highlight while retaining the current fast-scanning density.

### 5.5 Compact scaling

Preserve the current scale-aware geometry model. Structural target remains close to the present 440×420 logical size at `1.0×`; allow a modest increase only if the new status strip genuinely requires it.

## 6. Theme system v2

Keep exactly three core themes at v0.6 launch:

- Dark
- Light
- PokeMMO

Refactor theme data from a handful of generic colours into reusable semantic tokens while preserving backwards compatibility during migration.

Suggested token groups:

- root/background;
- panel/card surface;
- elevated surface;
- input surface;
- border/subtle border;
- primary text;
- secondary/muted text;
- accent/selection;
- ready;
- waiting;
- cooldown;
- unknown;
- money;
- next-route background/border;
- detector info/pay/battle;
- scrollbar/hover.

### Dark

Charcoal/slate baseline matching the approved concept. Muted olive/gold route selection.

### Light

Off-white/light-grey surfaces with slate text. Do not simply invert Dark. Status colours remain recognizable but toned for light backgrounds.

### PokeMMO

Warmer, slightly game-flavoured dark palette with controlled orange/blue-green accents. It should feel more PokeMMO-like than Dark without becoming loud.

## 7. Future background/skin architecture

Do not make decorative backgrounds a blocker for v0.6.0. Build the hook now and add skins later.

State concept:

- `background_skin: "Plain"` initially.

Future supported modes may include:

- Plain;
- Night Sky;
- Route Map Inspired;
- Custom Local Image.

Rules:

- dashboard cards remain readable and sufficiently opaque;
- background scales/crops independently from UI Scale;
- Compact stays plain and does not use decorative background art;
- no runtime image downloads.

## 8. Proposed module architecture

Keep core/tracking modules unchanged wherever possible.

Suggested presentation modules:

```text
app/tracker/
├── dashboard_ui.py          # Full dashboard composition / controller
├── dashboard_components.py  # cards, fields, pills, gym rows, detector rows
├── compact_ui.py            # compact mini-dashboard
├── themes.py                # semantic theme tokens / 3 core themes
├── ui_assets.py             # money icon + small project-owned UI icons
├── leader_art.py            # original leader portrait rendering/data
├── leader_art_integration.py
├── scaling.py               # shared scale helpers/controller
└── ui.py                    # legacy app/controller shell during migration
```

`presentation.py` and the existing earnings-strip decoration should be retired only after the dashboard is feature-complete and validated.

The offline earnings calculator may remain a separate Toplevel initially, but it should inherit theme tokens and `$` formatting.

## 9. Migration strategy

Do **not** replace the stable v0.5.5 presentation in one unreviewed commit.

Develop v0.6 on a feature branch with an explicit fallback until acceptance.

### Phase A — dashboard foundation

- semantic theme tokens;
- dashboard shell;
- status cards;
- controls card;
- temporary reuse of existing gym table if necessary;
- no engine changes.

Checkpoint: launch, filters, themes and scaling work.

### Phase B — custom gym list + portraits

- persistent `GymRow` components;
- scrollable dashboard gym list;
- larger original portraits;
- status pills;
- next-route highlight;
- payout column;
- manual selection/actions.

Checkpoint: live one-second timer updates without flicker; route/filter changes correct.

### Phase C — earnings + money presentation

- integrated Run Earnings card;
- `$` formatter throughout visible UI;
- project-owned stacked-coin icon;
- calculator restyle/format migration;
- Reset Run action.

Checkpoint: stored numeric values and calculation tests unchanged.

### Phase D — Detector dashboard

- structured event rows;
- type badges;
- Clear / auto-scroll behaviour if useful;
- responsive sizing / optional collapse.

Checkpoint: all existing event messages still surface.

### Phase E — Compact mini-dashboard

- themed header/chrome;
- aligned filters retained;
- segmented status strip;
- optional Actual run money indicator;
- dashboard-style compact table;
- preserve always-on-top / drag / restore / close / saved geometry.

Checkpoint: usable at every UI scale and narrow sizes.

### Phase F — cleanup

- remove obsolete Full-view decoration code only after dashboard acceptance;
- update README / ARCHITECTURE / Project Handoff;
- full Windows Actions build;
- real screenshot comparison at Dark, Light, PokeMMO and several scale values.

## 10. Scaling requirements

v0.6 must preserve the current explicit app-controlled scaling model. Do not use global Tk `tk scaling`.

Acceptance scales:

- `0.85×`
- `1.0×`
- `1.25×`
- `1.5×`
- `1.75×`
- `2.0×`

Every reusable dashboard component must consume the shared scale helper rather than embedding arbitrary pixel constants that cannot scale.

Portraits, icons, card padding, status pills, row heights, borders, controls and compact chrome all scale from logical `1.0×` dimensions.

## 11. Performance / refresh requirements

- no OCR, screen capture, memory access, client hooks or new network calls;
- avoid redrawing/recreating the entire dashboard every second;
- update timer/status text in persistent components;
- row list may rebuild on filter/route/data-membership changes, not every tick;
- cache generated portraits/icons per theme + scale;
- keep CPU impact negligible in normal rerun use.

## 12. Testing / acceptance criteria

A v0.6 release candidate is accepted only when all of the following are true:

1. Existing parser/earnings/scaling regression suite remains green.
2. New presentation tests cover theme token completeness and money formatting.
3. Windows PyInstaller build launches normally.
4. Dark, Light and PokeMMO are visually usable at `1.0×`, `1.25×`, `1.5×` and `2.0×`.
5. `0.85×` remains functional without clipping critical controls.
6. Route ordering/filtering is identical to v0.5.5 behaviour.
7. Live cooldown text updates without portrait/row flicker.
8. `Need N battle(s)` / `00:00:00` behaviour is preserved.
9. Next-route highlighting remains correct.
10. Manual correction actions operate on the selected dashboard row.
11. Earnings totals equal existing v0.5.5 calculations.
12. UI money presentation uses stacked-coin icon + `$` convention consistently.
13. Detector remains visible/reachable at realistic Windows window heights.
14. Compact retains drag, always-on-top, restore, close and saved position/size.
15. Compact remains useful over the game and does not become visually overloaded.
16. No integration/compliance boundary changes are introduced.

## 13. Explicit non-goals for v0.6.0

Do not delay the dashboard release for:

- official/ripped Gym Leader sprites;
- online price APIs;
- animated backgrounds;
- route-map downloads;
- a large bottom navigation system with pages that do not yet exist;
- a full charting/analytics subsystem;
- redesigning the tracker engine.

## 14. Definition of done

v0.6 is complete when the new Full dashboard and Compact mini-dashboard replace the old presentation in normal use, retain all validated tracker behaviour, work across the three core themes and supported scale values, and visually match the approved concept direction closely enough that v0.5.5 is no longer needed as the normal UI fallback.
