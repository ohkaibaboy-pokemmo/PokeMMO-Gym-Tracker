# PokeMMO Gym Tracker — Project Handoff

**Last updated:** 2026-08-28  
**Public branch:** `main`  
**Released tag:** `v0.6.0`  
**Status:** public unsigned v0.6 release published and validated / SignPath Foundation application next  
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
- release publishing isolated to the tag-only job with `contents: write`;
- GitHub Actions pinned to immutable commit SHAs;
- checkout credentials not persisted;
- build dependencies pinned in `requirements-build.txt`;
- Windows artifact uploaded before release publication, matching the intended SignPath origin-verification path.

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

The prerequisite public release required by the project's adopted application flow is complete. Current SignPath Open Source requirements use a Trusted Build System and origin verification. The existing GitHub-hosted workflow already builds and stores the release artifact through GitHub Actions, which is the intended integration architecture.

Next sequence:

1. submit the SignPath Foundation application for `ohkaibaboy-pokemmo/PokeMMO-Gym-Tracker`, referencing public release `v0.6.0`;
2. wait for acceptance and the actual SignPath organization/project/signing-policy/artifact-configuration identifiers;
3. install/authorize the SignPath GitHub App as instructed and add the trusted GitHub build-system/origin-verification integration;
4. do **not** invent `.signpath/policies/...` project or policy slugs before SignPath supplies them;
5. build a signed Windows candidate through GitHub-hosted Actions;
6. validate download -> extract -> launch and confirm Windows shows the expected publisher/signature;
7. run final post-signing regression/sign-off and update the public release.

## Starting a new conversation

Use:

> Continue development/release work for my PokeMMO Gym Tracker. Repo: `ohkaibaboy-pokemmo/PokeMMO-Gym-Tracker`. Read `PROJECT_HANDOFF.md`, `V060_TEST_PLAN.md`, `ARCHITECTURE.md`, `V060_DASHBOARD_SPEC.md`, and current GitHub source before making changes. Treat this public GitHub repository as the app source of truth. For 6 Pillows route/testing information, use the PokeMMO 30-Gym Rerun Test Tracker Project Handoff/latest test tab as the source of truth.
