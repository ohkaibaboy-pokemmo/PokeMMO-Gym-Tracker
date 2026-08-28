# PokeMMO Gym Tracker — Project Handoff

**Last updated:** 2026-08-28  
**Public branch:** `main`  
**Target:** `v0.6.0`  
**Status:** public source + governance green / prerequisite release + SignPath pending  
**Latest validated Windows package pipeline:** build 45 / run `33189191371` in the retained private development archive

Read this before continuing release work.

## Source of truth

This public GitHub repository is the source of truth for the Gym Tracker app's public source, architecture, build pipeline and release configuration. `V060_TEST_PLAN.md` is the formal v0.6 release gate.

The repository was created from the audited v0.6 source snapshot rather than publishing the old development Git history, because historical author/committer metadata in the private archive contained a personal email address. The public repository starts with a clean history and GitHub `noreply` commit identity. The private development archive is not to be made public.

For the separate **6 Pillows / gym rerun strategy**, use the Google Sheet **PokeMMO 30-Gym Rerun Test Tracker**, especially **Project Handoff** and the latest test tab, as the current source of truth. Prefer real test evidence over older theoretical ideas.

## Project boundary

The tracker is a lightweight standalone Windows companion for Gym Leader cooldowns, the five-other-trainer rule, routes, earnings and recent detected log activity.

Data path:

`PokeMMO local chat log -> tracker parser/state -> dashboard`

It does **not** inject into PokeMMO, read process memory, hook functions, inspect packets, capture the screen, use OCR, automate input, modify the game client or require runtime external APIs.

Vanilla PokeMMO log output is the canonical parser contract. Third-party string-mod support is best-effort and has representative live validation.

Do not commit raw user chat logs. Tests use sanitized fictional data.

## Current runtime architecture

The active runtime is `app/main.pyw` plus `app/tracker/`. Legacy version-stamped monolithic Python files and the abandoned Go experiment were deliberately excluded from the clean public repository.

Important modules include:

- `tracker/engine.py` — parsing, victories, cooldowns, five-rule, payouts and replay events.
- `tracker/logs.py` — live tailing, including stable EOF handling.
- `tracker/async_replay.py` — responsive batched replay.
- `tracker/state.py` — persistence/migrations in LocalAppData.
- `tracker/earnings.py` / `earnings_ui.py` — actual/projected earnings.
- `tracker/dashboard_full_refresh.py` — Full header/KPIs.
- `tracker/dashboard_earnings_split.py` — Run Earnings KPI + Run Details support card.
- `tracker/dashboard_gym_list.py` — single-Canvas Full Gym Route backed by the hidden Treeview model.
- `tracker/dashboard_resize_smoothing.py` — safe Full resize floor plus whole-row route bottom edge.
- `tracker/dashboard_detector.py` / `dashboard_detector_polish.py` — Detector presentation and replay lifecycle.
- `tracker/user_assets.py` and override modules — portable art beside the EXE.
- `tracker/compact_ui.py`, `compact_type_icons.py`, `compact_row_snap.py` — Compact presentation.

### Manual state mutation

v0.6 intentionally exposes **no manual Gym-state mutation controls**. Replay is the recovery mechanism for missed ingestion. A narrow reconstruction safeguard remains for identifiable fractional-second synthetic leader events created during earlier private v0.6 testing; this is repair logic, not a user feature.

## Adopted dashboard direction

Preserve the accepted Full hierarchy:

**Header/KPIs -> Controls -> Gym Route -> Detector**

Headline cards: **Ready | Waiting | Cooldown | Run Earnings**. Run Details contains Route base / Actual run / Route gyms / Other payouts. At narrow widths Run Details reflows to its own full-width row rather than clipping.

Full route rows remain:

**Portrait -> # -> Type + Leader -> Gym -> Region -> 5-rule -> Cooldown -> Last Defeated -> Status -> Payout**

Compact remains a rerun overlay rather than a miniature Full dashboard. Preserve its stable in-place sync, frameless/draggable/always-on-top behaviour and complete-row snapping.

## Five-rule / cooldown semantics

Adopted counting model is opt-out:

- every detected normal trainer victory counts toward all currently active Gym requirements by default;
- only explicitly excluded trainers fail to count;
- a different Gym Leader counts toward other active gyms;
- the just-defeated Gym Leader does not count toward its own newly reset requirement;
- count caps at `5/5`.

Cooldown is 18 hours per character. Active timer = COOLDOWN; expired timer + incomplete rule = WAITING; expired timer + `5/5` = READY. PokeMMO's rematch rejection is authoritative evidence and emits a WARN Detector event.

### Bugsy / PI Carlos regression — resolved

Earlier private testing produced a false Bugsy `5/5 READY` because manual UI testing had inserted synthetic fractional-second Gym Leader events into saved five-rule history. v0.6 removed user-facing mutation and ignores those identifiable legacy synthetic events during reconstruction.

Live reconciliation repaired Bugsy to `4/5 WAITING`; the genuine four qualifying events were **PI Carlos, Socialite Marian, Leader Gardenia and Leader Lt. Surge**. Gentleman Yan moved Bugsy to `5/5`, after which PokeMMO allowed the rematch. Conclusion: repaired tracker state matched the server and **PI Carlos counted**. Do not reopen a Carlos exclusion theory without new empirical evidence.

## Live tail / replay

Stable unterminated EOF records are processed after two unchanged polls without committing the file position; growing partial records remain deferred. Replay is asynchronous and same-file replay replaces its prior Detector replay session while persistent victory/payout state remains de-duplicated.

Representative live string-mod validation passed for normal trainers, Gym wins/cooldowns, payouts and the five-battle block warning.

## Earnings semantics

- `Reset Run` advances the accounting window without deleting payout history.
- gold row payout means empirical payout in the current run window.
- Run Earnings = current actual run.
- ordinary trainer payouts contribute to Other payouts.
- selected-route Gym payouts contribute to route progress once.

Known route bases:

- All gyms: `$367,744`
- `6 Pillows — Current 30`: `$268,632`

## Portable local art

Packaged layout:

```text
PokeMMO Gym Tracker.exe
custom/
├── type_icons/
└── leader_sprites/
```

LocalAppData remains for state/settings only. Missing or invalid overrides fall back to built-in original art.

## CI / packaging

The clean public repository keeps the hardened release workflow on GitHub-hosted runners:

- default `contents: read`;
- release publishing isolated to the tag-only job with `contents: write`;
- GitHub Actions pinned to immutable commit SHAs;
- checkout credentials not persisted;
- build dependencies pinned in `requirements-build.txt`;
- Windows artifact uploaded before release publication, matching the path needed for later SignPath origin verification.

Private build 45 / run `33189191371` passed the same hardened source/tooling path: regression tests, pinned build-tool installation, Windows onefile build, icon verification, ZIP packaging and artifact upload. No app-runtime code changed as part of the public-history cleanup.

The clean public `main` source has also passed its GitHub-hosted regression workflow after import. The ordinary `main` push correctly runs the Linux regression job while skipping Windows packaging/release publication.

## Public-repository privacy result

The old private repository's historical commit metadata contained a personal email. Rather than expose or rely on a complex history rewrite, the public repository was created from an audited tracked-source snapshot.

Before import, the snapshot was checked for personal email addresses, local Windows user paths, private keys, common GitHub/AWS credential patterns, generic secret assignments and tracked log/state/build artifacts; none were found. Legacy versioned source files and the abandoned Go experiment were omitted from the public tree.

Future GitHub commits use the account's GitHub `noreply` identity.

## Repository governance

Public-repository governance is now in place:

- active repository ruleset **Protect main** targets the default branch;
- branch deletion is restricted;
- non-fast-forward / force-push updates are blocked;
- private vulnerability reporting was enabled by the repository owner on 2026-08-28.

The GitHub API confirms the active ruleset and its deletion/non-fast-forward rules. The private-vulnerability-reporting toggle is recorded from the owner's completed settings change because the current connector does not expose that account/repository security setting for verification.

## Signing / release status

Selected direction: **SignPath Foundation**, assuming project acceptance. `CODE_SIGNING.md`, `SECURITY.md`, `CODEOWNERS`, pinned build dependencies and least-privilege workflows are present.

SignPath Foundation's current OSS conditions require the project to already be released in the form that should be signed. The public repository therefore needs one normal unsigned Windows release before the application is submitted. Future SignPath Open Source signing must use a Trusted Build System with origin verification; the GitHub path is already the adopted architecture.

Adopted next sequence:

1. publish the prerequisite public Windows release from the current clean `main` source;
2. verify the tag workflow builds/tests and the GitHub release contains the expected Windows ZIP;
3. apply to SignPath Foundation;
4. after acceptance, add the actual SignPath project/policy identifiers and origin-verification signing integration — do not invent `.signpath` slugs before they are supplied;
5. build and test the signed Windows candidate on normal current Windows;
6. complete the final release-head regression/sign-off;
7. publish the final signed v0.6 release/update.

## Starting a new conversation

Use:

> Continue development/release work for my PokeMMO Gym Tracker. Repo: `ohkaibaboy-pokemmo/PokeMMO-Gym-Tracker`. Read `PROJECT_HANDOFF.md`, `V060_TEST_PLAN.md`, `ARCHITECTURE.md`, `V060_DASHBOARD_SPEC.md`, and current GitHub source before making changes. Treat this public GitHub repository as the app source of truth. For 6 Pillows route/testing information, use the PokeMMO 30-Gym Rerun Test Tracker Project Handoff/latest test tab as the source of truth.
