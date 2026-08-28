# PokeMMO Gym Tracker — v0.6 Release Validation Plan

**Branch:** `main`  
**Target:** v0.6.0  
**Last updated:** 2026-08-28  
**Latest public-source regression:** run `33212337473` — PASS  
**Latest validated Windows package pipeline:** build 45 / run `33189191371` in the retained private development archive

## Status legend

- `[x] AUTO` — automated regression coverage passed.
- `[x] LIVE` — directly observed working in the Windows artifact/game.
- `[x] DECISION` — release decision adopted.
- `[x] PREP` — repository/release preparation completed.
- `[ ] WIN` — Windows/manual validation still required.
- `[ ] RELEASE` — public-release/distribution work still required.

## Release gate

The public source repository is established and the v0.6 runtime/regression evidence is green. Do not call v0.6 a finished signed Windows release until all remaining release items are complete:

- [x] AUTO Clean public `main` regression workflow is green (`33212337473`).
- [x] PREP Public repository begins from an audited source snapshot rather than the old private development history.
- [x] PREP Current GitHub commits use the account's GitHub `noreply` identity.
- [x] PREP Hardened public workflow uses pinned actions/build dependencies and least-privilege permissions.
- [x] Latest deliberately requested Windows validation artifact built successfully (private build 45).
- [x] Build 45 validated pinned build-tool installation, immutable action pins, onefile build, icon verification, ZIP packaging and artifact upload.
- [x] No open blocker/high-severity regression is known in cooldowns, five-rule counting, replay, earnings, state persistence, Full view or Compact view.
- [x] Representative Full theme/scale matrix is complete.
- [x] Compact, scrolling, replay, local-art overrides, earnings and live parser scenarios are complete.
- [x] Representative string-mod compatibility is complete.
- [ ] RELEASE A normal prerequisite public release exists for the adopted SignPath Foundation application flow.
- [ ] RELEASE SignPath Foundation application/acceptance and origin-verified GitHub signing integration are complete.
- [ ] WIN A signed/known-publisher Windows candidate passes download → extract → launch validation on normal current Windows.
- [ ] AUTO Final post-signing release-head regression is green.

## Automated regression suite

```bash
python -m py_compile app/main.pyw
python -m compileall -q app/tracker
python -m unittest discover -s tests -v
```

The clean public repository passed this regression path in run `33212337473`. The Windows artifact and release jobs correctly skipped on the ordinary `main` push; Windows packaging remains deliberate via manual dispatch or release tag.

### Parser / cooldown / five-rule

- [x] AUTO Vanilla Gym Leader challenge/victory parsing.
- [x] AUTO Confirmed Gym win starts an 18-hour cooldown and own requirement at `0/5`.
- [x] AUTO Ordinary normal trainer wins count by default toward active five-rule requirements.
- [x] AUTO Explicitly excluded trainers do not count.
- [x] AUTO Different Gym Leader counts for other active gyms but not its own fresh requirement.
- [x] AUTO Duplicate victories are ignored.
- [x] AUTO PokeMMO's five-battle rematch rejection emits WARN.
- [x] AUTO Identifiable legacy fractional-timestamp synthetic manual Gym events are excluded from five-rule reconstruction.
- [x] AUTO User-facing manual Gym-state mutation is removed from the v0.6 startup/dashboard path.

### Payouts / earnings

- [x] AUTO `$` payouts link to the preceding victory and de-duplicate.
- [x] AUTO Historical payout backfill works.
- [x] AUTO `Reset Run` starts a fresh accounting window without deleting history.
- [x] AUTO Route-gym and other-trainer payouts remain separated.
- [x] AUTO Visible money presentation uses `$`.

### Replay / live tail

- [x] AUTO Replay reconstructs useful BATTLE → GYM/WIN → PAY presentation without duplicating persistent state.
- [x] AUTO Async replay remains bounded/responsive and resumes live tail.
- [x] AUTO Same-file replay replaces the prior Detector replay session rather than stacking duplicates.
- [x] AUTO Short Detector histories bottom-anchor.
- [x] AUTO Stable unterminated EOF records are processed after two unchanged polls.
- [x] AUTO Growing partial EOF records remain deferred until stable/complete.

### Full / Compact presentation

- [x] AUTO Themes remain Dark / PokeMMO / Light.
- [x] AUTO Supported UI scales remain 0.85×, 1.0×, 1.25×, 1.5×, 1.75×, 2.0×.
- [x] AUTO Full uses the lightweight single-Canvas Gym Route renderer.
- [x] AUTO Detector uses direct Canvas primitives.
- [x] AUTO Full whole-row bottom-gap calculation prevents a visibly clipped final Gym row.
- [x] AUTO Responsive-header breakpoint keeps Run Details in the top row when wide and moves it to a full-width second row when narrow.
- [x] AUTO Compact stable-row sync and final-layout row snap remain covered.

## Windows UI validation

### Full baseline

- [x] LIVE Full hierarchy/semantics accepted.
- [x] LIVE Canvas resize architecture accepted; no return to the earlier throttle/debounce approach.
- [x] LIVE Minimise/restore preserves usable layout/state.
- [x] LIVE Portraits, type markers, region, five-rule, cooldown, status and payout presentation remain aligned.
- [x] LIVE Manual Correction controls are removed; tracker state is log-derived.
- [x] LIVE Build 43: Full Gym Route ends on a complete row with no partial next row visible.
- [x] LIVE Build 44: at roughly half-monitor width, Run Details reflows instead of clipping.

Build 45 introduced no intended app-runtime behaviour change after the live-tested runtime; it validated the hardened CI/package path.

### Theme / scale matrix

| Theme | 0.85× | 1.0× | 1.5× | 2.0× |
| --- | --- | --- | --- | --- |
| Dark | [x] LIVE | [x] LIVE | [x] LIVE | [x] LIVE |
| PokeMMO | [x] LIVE | [x] LIVE | [x] LIVE | [x] LIVE |
| Light | [x] LIVE | [x] LIVE | [x] LIVE | [x] LIVE |

### Scrollbars / Compact / art

- [x] LIVE Full Gym Route and Detector wheel/thumb/page scrolling.
- [x] LIVE Compact `COMPACT-01`..`COMPACT-08`.
- [x] LIVE Portable `custom/type_icons` and `custom/leader_sprites` behaviour.
- [x] LIVE Same-file replay presentation de-duplication and bottom anchoring.

## Real PokeMMO functional validation

### Live log / cooldown / five-rule

- [x] LIVE Normal trainer BATTLE/WIN detection.
- [x] LIVE Gym BATTLE/GYM/PAY detection.
- [x] LIVE Fresh Gym win starts 18 hours and own `0/5`.
- [x] LIVE Ordinary trainer increments active requirements.
- [x] LIVE Different Gym Leader counts for other active requirements.
- [x] LIVE Count caps at `5/5`.
- [x] LIVE Expired timer + incomplete rule shows WAITING / `Need N battle(s)`.
- [x] LIVE Timer + five wins complete shows READY.
- [x] LIVE Server five-battle rejection produces WARN.

### Bugsy / PI Carlos state-repair regression — resolved 2026-08-28

Earlier manual UI testing had polluted saved five-rule history with synthetic fractional-second Gym Leader events. The repaired v0.6 runtime removed user-facing mutation and excludes those identifiable synthetic events during reconstruction.

Bugsy repaired from false `5/5 READY` to `4/5 WAITING`. The four genuine qualifying events were **PI Carlos + Socialite Marian + Leader Gardenia + Leader Lt. Surge**. Gentleman Yan then moved Bugsy `4/5 → 5/5`, and PokeMMO subsequently allowed the Bugsy rematch. Therefore the repaired tracker state matched the server and **PI Carlos was a valid qualifying battle**.

### Earnings / state

- [x] LIVE Fresh `Reset Run` accounting.
- [x] LIVE Gym payout counted once.
- [x] LIVE Normal trainer payout goes to Other Payouts.
- [x] LIVE Route progress only for selected-route gyms.
- [x] LIVE Multi-gym payout reconciliation.
- [x] LIVE Character-specific cooldown/five-rule and earnings state.
- [x] LIVE Restart persistence and fresh launch to Full.

## String-mod compatibility

- [x] LIVE `MOD-01` normal trainer challenge/victory.
- [x] LIVE `MOD-02` Gym Leader challenge/victory + 18h cooldown.
- [x] LIVE `MOD-03` payout detection/linking.
- [x] LIVE `MOD-04` five-battle block warning.
- [x] LIVE `MOD-05` no representative grammar failure found.

Representative evidence includes Socialite Marian BATTLE → WIN → PAY `$5,400`, Gardenia/Eterna BATTLE → GYM → PAY `$8,736` with own `0/5` and fresh cooldown, and the PokeMMO five-rule warning. The earlier PI Carlos payout miss was a generic live-tail EOF issue; replay recovered it and the stable-EOF fix was live-confirmed.

## Windows packaging / code signing

- [x] LIVE `PKG-01` Onefile ZIP contents are acceptable.
- [x] LIVE `PKG-02` Onefile download/extraction experience is preferred over folder builds.
- [x] DECISION `PKG-03` Microsoft false-positive submission is not being pursued; current builds are no longer being classified as malware and the remaining Windows trust issue is Unknown publisher.
- [x] DECISION `PKG-04` Code-signing options evaluated. Selected direction: **SignPath Foundation**, assuming acceptance.
- [ ] RELEASE `PKG-05` Final public package still needs signed/known-publisher download → extract → launch validation.

### Build 45 — hardened package validation

Private development run `33189191371` passed:

- [x] AUTO Regression tests.
- [x] PREP Pinned `requirements-build.txt` installation.
- [x] PREP Immutable-pinned GitHub Actions.
- [x] PREP Windows onefile build.
- [x] PREP Embedded icon verification.
- [x] PREP ZIP packaging and artifact upload.

### Public-repository readiness — completed

- [x] PREP `CODE_SIGNING.md`, `SECURITY.md` and `.github/CODEOWNERS` are present.
- [x] PREP Windows build dependencies are pinned in `requirements-build.txt`.
- [x] PREP GitHub Actions are pinned to immutable commit SHAs.
- [x] PREP Default workflow permissions are read-only; release publication alone receives `contents: write`.
- [x] PREP Checkout credentials are not persisted in normal build/test jobs.
- [x] PREP README reflects v0.6 semantics, `$` presentation, portable `custom/` art and signing status.
- [x] PREP Public source excludes superseded versioned Python prototypes, the abandoned Go experiment and private build-trigger workflow.
- [x] PREP Audited source contains no tracked raw logs/state/build artifacts and no detected personal email, local Windows user path, private-key or common credential patterns.
- [x] PREP Public history does not include the old private development history; current commits use GitHub `noreply` identity.
- [x] AUTO Clean public `main` regression run `33212337473` passed.

### SignPath Foundation plan

Adopted project sequence:

`clean public repo → prerequisite public release → SignPath Foundation application → GitHub origin verification/signing integration → signed v0.6 candidate → final Windows validation → final release`

The prerequisite public-release step is the project's adopted application sequence; do not present it as a universal SignPath rule. Do not invent `.signpath/policies/...` identifiers before SignPath supplies the actual project/signing-policy slugs.

All jobs leading to the intended signing request remain on GitHub-hosted runners, and the workflow uploads the Windows artifact before release publication so it can later be handed to the SignPath signing request with origin verification.

## Release-candidate sign-off record

- **Public source/privacy audit:** PASS
- **Public Git commit identity:** PASS (`noreply`)
- **Public `main` regression:** PASS — run `33212337473`
- **Private build 45 regression/package pipeline:** PASS — run `33189191371`
- **Full-view UI:** PASS
- **Compact UI:** PASS
- **Scrollbars:** PASS
- **Portable art overrides:** PASS
- **Replay responsiveness/presentation:** PASS
- **Vanilla live functional tests:** PASS
- **Fresh Reset Run / earnings rerun:** PASS
- **String-mod representative tests:** PASS
- **Bugsy/Carlos five-rule reconciliation:** PASS
- **Public prerequisite release:** PENDING
- **SignPath acceptance/integration:** PENDING
- **Signed Windows validation:** PENDING
- **Final post-signing release-head regression:** PENDING
