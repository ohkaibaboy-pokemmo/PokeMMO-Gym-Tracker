# PokeMMO Gym Tracker — Project Handoff

**Last updated:** 2026-08-29  
**Public branch:** `main`  
**Released tag:** `v0.6.0`  
**Status:** public unsigned v0.6 release published / external-test portability hotfix validated on an external 1920×1080 Windows setup / SignPath Foundation application next  
**Latest hotfix regression:** run `33258276374` — PASS  
**Latest Windows candidate:** run `33258556273` — PASS / externally live-validated  
**Public release workflow:** run `33213551249` — PASS  
**Release asset:** `PokeMMO-Gym-Tracker-windows-x64.zip` — SHA-256 `2ce87dd8ae9939336a9a866e2921c94d1bcb1ec8753670686043a538482e3915`

Read this before continuing release/signing work.

## Source of truth

This public GitHub repository is the source of truth for the Gym Tracker app's public source, architecture, build pipeline and release configuration. `V060_TEST_PLAN.md` remains the detailed v0.6 validation record.

The public repository was created from an audited v0.6 source snapshot rather than publishing the old development Git history, because historical author/committer metadata in the private archive contained a personal email address. Public history uses the account's GitHub `noreply` identity. The private development archive must remain private.

For the separate **6 Pillows / gym rerun strategy**, use the Google Sheet **PokeMMO 30-Gym Rerun Test Tracker**, especially **Project Handoff** and the latest test tab, as the current source of truth. Prefer real test evidence over older theoretical ideas.

## Project boundary

The tracker is a standalone Windows companion for Gym Leader cooldowns, the five-other-trainer rule, routes, earnings and recent detected log activity.

Data path:

`PokeMMO local chat log -> tracker parser/state -> dashboard`

It does **not** inject into PokeMMO, read process memory, hook functions, inspect packets, capture the screen, use OCR, automate input, modify the game client or require runtime external APIs.

Vanilla PokeMMO log output is the canonical parser contract. Third-party string-mod support is best-effort and has representative live validation. Do not commit raw user chat logs; tests use sanitized fictional data.

## Current runtime architecture

The active runtime is `app/main.pyw` plus `app/tracker/`. Legacy version-stamped monolithic Python files and the abandoned Go experiment were deliberately excluded from the clean public repository.

Important modules include:

- `tracker/engine.py` — parsing, victories, cooldowns, five-rule, payouts and replay events.
- `tracker/logs.py` — live tailing, including stable EOF handling.
- `tracker/async_replay.py` — responsive batched replay.
- `tracker/state.py` — persistence/migrations in LocalAppData.
- `tracker/earnings.py` / `earnings_ui.py` — actual/projected earnings.
- `tracker/dashboard_full_refresh.py`, `dashboard_gym_list.py`, `dashboard_resize_smoothing.py` — Full dashboard.
- `tracker/dashboard_detector.py` / `dashboard_detector_polish.py` — Detector presentation and replay lifecycle.
- `tracker/layout_visibility_guard.py` — prevents scale passes from remapping presentation widgets that were deliberately hidden with `pack_forget` / `grid_forget`.
- `tracker/user_assets.py` and override modules — portable local art.
- `tracker/compact_ui.py`, `compact_type_icons.py`, `compact_row_snap.py` — Compact presentation.

v0.6 intentionally exposes **no manual Gym-state mutation controls**. Replay is the recovery mechanism for missed ingestion. A narrow reconstruction safeguard remains for identifiable fractional-second synthetic leader events created during earlier private v0.6 testing; this is repair logic, not a user feature.

## Adopted UI / gameplay semantics

Preserve the accepted Full hierarchy:

**Header/KPIs -> Controls -> Gym Route -> Detector**

Headline cards: **Ready | Waiting | Cooldown | Run Earnings**. Run Details contains Route base / Actual run / Route gyms / Other payouts. Compact remains a rerun overlay rather than a miniature Full dashboard.

Five-rule counting model is opt-out:

- every detected normal trainer victory counts toward all currently active Gym requirements by default;
- only explicitly excluded trainers fail to count;
- a different Gym Leader counts toward other active gyms;
- the just-defeated Gym Leader does not count toward its own newly reset requirement;
- count caps at `5/5`.

Cooldown is 18 hours per character. Active timer = COOLDOWN; expired timer + incomplete rule = WAITING; expired timer + `5/5` = READY. PokeMMO's rematch rejection is authoritative evidence and emits a WARN Detector event.

### External tester portability regression — resolved 2026-08-29

A first external-user test exposed two post-release portability issues that were not visible on the primary development machine.

**Tracking failure:** the app successfully selected and watched the tester's PokeMMO chat log, but every battle line was ignored. Their vanilla Windows log used the US timestamp form `M/D/YY h:mm:ss AM/PM`, while the parser contract only accepted the previously validated UK-style `DD/MM/YYYY HH:MM:SS`. The hotfix keeps the accepted UK grammar and adds the empirically observed US 12-hour forms. Regression coverage uses a sanitized fictional reproduction of the external Flannery challenge -> player send-out -> victory -> payout sequence; the raw user log is not committed.

**Full-header corruption:** the original tester screenshot showed the passive live-log status twice and the retired mixed-purpose earnings card resurfacing beneath the headline KPIs. Root cause: the scaling controller captured baseline pack/grid padding before later presentation layers deliberately called `pack_forget()` / `grid_forget()`. A subsequent scaling pass could call `pack_configure()` / `grid_configure()` on those now-unmanaged widgets, which remapped them and distorted the KPI layout. `layout_visibility_guard.py` now withholds unmanaged/mismatched widgets from a scaling pass without deleting their baseline metadata, so a widget can still scale normally if it is deliberately managed again later.

The hotfix was merged to `main` at commit `6a5f9e73a7c5801a8968ce1652b9f4a9acdecd96`; public regression workflow run `33258276374` passed. The chat-retrievable Windows-artifact workflow was then enabled on `main`, and candidate run `33258556273` passed regression, Windows build, icon verification, packaging and artifact upload.

**External validation PASS:** the same external tester, on a reported 1920×1080 Windows setup, ran the fresh fixed candidate at UI Scale `1.0×`. Live US-format tracking was visibly working across consecutive Gym battles: Brycen was detected, defeated and paid `$14,577`; Iris was then detected, defeated and paid `$14,742`; the dashboard showed two active cooldowns and Brycen correctly advanced to `1/5` while Iris began at `0/5`. The header no longer duplicated the live-log status, the retired earnings card did not reappear, and Run Details remained readable at the default scale. This closes the portability hotfix; do not change the responsive-header breakpoint based on the original corrupted screenshot unless new evidence appears.

### Bugsy / PI Carlos regression — resolved

Earlier private testing produced a false Bugsy `5/5 READY` because manual UI testing had inserted synthetic fractional-second Gym Leader events into saved five-rule history. v0.6 removed user-facing mutation and ignores those identifiable legacy synthetic events during reconstruction.

Live reconciliation repaired Bugsy to `4/5 WAITING`; the genuine four qualifying events were **PI Carlos, Socialite Marian, Leader Gardenia and Leader Lt. Surge**. Gentleman Yan moved Bugsy to `5/5`, after which PokeMMO allowed the rematch. Conclusion: repaired tracker state matched the server and **PI Carlos counted**. Do not reopen a Carlos exclusion theory without new empirical evidence.

## Earnings / route semantics

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

The public repository keeps the hardened release workflow on GitHub-hosted runners:

- default `contents: read`;
- pull requests run regression tests only;
- successful pushes to `main`, manual workflow dispatches and release tags produce a temporary Windows artifact;
- this means connected GitHub tooling can retrieve the latest validated Windows candidate directly from chat after a `main` change, without the user manually opening GitHub Actions;
- release publishing remains isolated to the tag-only job with `contents: write`;
- GitHub Actions pinned to immutable commit SHAs;
- checkout credentials not persisted;
- build dependencies pinned in `requirements-build.txt`;
- Windows artifact uploaded before release publication, matching the intended SignPath origin-verification path;
- normal `main` artifacts are retained for 7 days and do not create or replace a public GitHub Release.

The prerequisite public release is now complete:

- GitHub release **PokeMMO Gym Tracker v0.6.0** is public, not draft and not prerelease;
- tag `v0.6.0` points to public source commit `79a29fb1e9a068a5f8c9deb561a3fcd44bc58279`;
- release workflow run `33213551249` passed Regression tests, Windows artifact build and Publish GitHub Release;
- the Windows job passed checkout, pinned build-tool installation, icon generation, onefile PyInstaller build, embedded-icon verification, ZIP packaging and artifact upload;
- release asset `PokeMMO-Gym-Tracker-windows-x64.zip` is approximately 11.4 MB with SHA-256 `2ce87dd8ae9939336a9a866e2921c94d1bcb1ec8753670686043a538482e3915`.

This v0.6 release is intentionally **unsigned** while the project applies for SignPath Foundation open-source code signing.

## Public-repository privacy / governance

The old private repository's historical commit metadata contained a personal email. Rather than expose or rely on a complex history rewrite, the public repository was created from an audited tracked-source snapshot. The snapshot was checked for personal email addresses, local Windows user paths, private keys, common GitHub/AWS credential patterns, generic secret assignments and tracked log/state/build artifacts; none were found.

Repository governance is in place:

- active ruleset **Protect main** targets the default branch;
- branch deletion is restricted;
- non-fast-forward / force-push updates are blocked;
- private vulnerability reporting was enabled by the repository owner on 2026-08-28.

## Signing status / next sequence

Selected direction: **SignPath Foundation**, assuming project acceptance. `CODE_SIGNING.md`, `SECURITY.md`, `CODEOWNERS`, pinned build dependencies and least-privilege workflows are present.

The prerequisite public release required by the project's adopted application flow is complete, and the 2026-08-29 external-test portability hotfix is now externally validated. Current SignPath Open Source requirements use a Trusted Build System and origin verification. The existing GitHub-hosted workflow already builds and stores the release artifact through GitHub Actions, which is the intended integration architecture.

Next sequence:

1. submit the SignPath Foundation application for `ohkaibaboy-pokemmo/PokeMMO-Gym-Tracker`, referencing the current public release/source state;
2. wait for acceptance and the actual SignPath organization/project/signing-policy/artifact-configuration identifiers;
3. install/authorize the SignPath GitHub App as instructed and add the trusted GitHub build-system/origin-verification integration;
4. do **not** invent `.signpath/policies/...` project or policy slugs before SignPath supplies them;
5. build a signed Windows candidate through GitHub-hosted Actions;
6. validate download -> extract -> launch and confirm Windows shows the expected publisher/signature;
7. run final post-signing regression/sign-off and update the public release.

## Starting a new conversation

Use:

> Continue development/release work for my PokeMMO Gym Tracker. Repo: `ohkaibaboy-pokemmo/PokeMMO-Gym-Tracker`. Read `PROJECT_HANDOFF.md`, `V060_TEST_PLAN.md`, `ARCHITECTURE.md`, `V060_DASHBOARD_SPEC.md`, and current GitHub source before making changes. Treat this public GitHub repository as the app source of truth. For 6 Pillows route/testing information, use the PokeMMO 30-Gym Rerun Test Tracker Project Handoff/latest test tab as the source of truth.
