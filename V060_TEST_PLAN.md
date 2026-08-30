# PokeMMO Gym Tracker — v0.6 Release Validation Plan

**Branch:** `main`  
**Target:** v0.6.0  
**Last updated:** 2026-08-30  
**Latest hotfix regression:** run `33258276374` — PASS  
**Latest externally validated Windows candidate:** run `33258556273` — PASS / Defender heuristic detection confirmed on exact EXE hash

## Status legend

- `[x] AUTO` — automated regression coverage passed.
- `[x] LIVE` — directly observed working in the Windows artifact/game.
- `[x] DECISION` — release decision adopted.
- `[x] PREP` — repository/release preparation completed.
- `[ ] WIN` — Windows/manual validation still required.
- `[ ] RELEASE` — public-release/distribution work still required.

## Release gate

The public source repository, prerequisite v0.6.0 release, runtime regression evidence and external portability hotfix validation are green. Do not call v0.6 a finished signed Windows release until all remaining distribution items are complete:

- [x] AUTO Clean public `main` regression workflow is green.
- [x] PREP Public repository begins from an audited source snapshot rather than the old private development history.
- [x] PREP Current GitHub commits use the account's GitHub `noreply` identity.
- [x] PREP Hardened public workflow uses pinned actions/build dependencies and least-privilege permissions.
- [x] AUTO Hotfix regression run `33258276374` passed.
- [x] LIVE Windows candidate run `33258556273` passed build/package validation and external live testing.
- [x] No open blocker/high-severity regression is known in cooldowns, five-rule counting, replay, earnings, state persistence, Full view or Compact view.
- [x] Representative Full theme/scale matrix is complete.
- [x] Compact, scrolling, replay, local-art overrides, earnings and live parser scenarios are complete.
- [x] Representative string-mod compatibility is complete.
- [x] RELEASE A normal prerequisite public `v0.6.0` release exists for the adopted SignPath Foundation application flow.
- [x] LIVE Windows Defender `Trojan:Script/Wacatac.H!ml` detection was reproduced on the exact official fixed-candidate EXE hash `9f255ce832085500de983937ca964039cfa3e38ba4970d678eb582c01f275ea8`.
- [ ] RELEASE Microsoft software-developer sample submission has a final clean/acceptable determination or equivalent resolution for the Defender detection.
- [ ] RELEASE SignPath Foundation application/acceptance and origin-verified GitHub signing integration are complete.
- [ ] WIN A signed/known-publisher Windows candidate passes download → extract → launch plus Defender/SmartScreen validation on normal current Windows.
- [ ] AUTO Final post-signing release-head regression is green.

## Automated regression suite

```bash
python -m py_compile app/main.pyw
python -m compileall -q app/tracker
python -m unittest discover -s tests -v
```

The portability hotfix source passed this regression path in run `33258276374`. Windows candidate run `33258556273` then passed regression, Windows build, icon verification, ZIP packaging and artifact upload before external live validation.

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
- [x] AUTO UK-style timestamps remain supported.
- [x] AUTO Empirically observed US Windows `M/D/YY h:mm:ss AM/PM` log timestamps are supported.

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
- [x] AUTO Scale passes do not remap widgets deliberately hidden with `pack_forget()` / `grid_forget()`.

## Windows UI validation

### Full baseline

- [x] LIVE Full hierarchy/semantics accepted.
- [x] LIVE Canvas resize architecture accepted; no return to the earlier throttle/debounce approach.
- [x] LIVE Minimise/restore preserves usable layout/state.
- [x] LIVE Portraits, type markers, region, five-rule, cooldown, status and payout presentation remain aligned.
- [x] LIVE Manual Correction controls are removed; tracker state is log-derived.
- [x] LIVE Build 43: Full Gym Route ends on a complete row with no partial next row visible.
- [x] LIVE Build 44: at roughly half-monitor width, Run Details reflows instead of clipping.
- [x] LIVE External 1920×1080 test: duplicate Live status and retired earnings-card remapping are fixed at UI Scale `1.0×`.

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
- [x] LIVE External US-format log validation: Brycen detected/defeated/paid `$14,577`, then Iris detected/defeated/paid `$14,742`; Brycen advanced to `1/5` and Iris started at `0/5`.

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
- [x] LIVE `PKG-03` Windows Defender currently flags the exact official unsigned fixed-candidate EXE as `Trojan:Script/Wacatac.H!ml`; local SHA-256 was confirmed identical to official candidate hash `9f255ce832085500de983937ca964039cfa3e38ba4970d678eb582c01f275ea8`. Treat as unresolved until Microsoft determines the software-developer submission; do not whitelist the candidate for distribution.
- [x] DECISION `PKG-04` Code-signing options evaluated. Selected direction: **SignPath Foundation**, assuming acceptance.
- [ ] RELEASE `PKG-05` Final public package still needs signed/known-publisher download → extract → launch validation, including Defender and SmartScreen.

### Confirmed candidate provenance — 2026-08-30

Official fixed candidate from GitHub Actions run `33258556273`, commit `2817d637d7320b518cbfbf66fd893d9c42826b30`:

- GitHub Actions artifact SHA-256 `d422485e7d8bc4728f834ea78c33ac9694c200178b2686c158c5beb20180a623`;
- packaged inner ZIP SHA-256 `82e641a6746b06e7408eb56ec345ec90ec2d8338bf991ab38a3514f07fe9b4e8`;
- EXE SHA-256 `9f255ce832085500de983937ca964039cfa3e38ba4970d678eb582c01f275ea8` — user-confirmed identical to the Defender-detected local EXE.

The EXE is currently unsigned. Matching the official hash rules out an unknown modified local copy as the explanation for this detection, but does not itself prove whether Microsoft's classification is correct. Submit the exact file to Microsoft Security Intelligence as **Software developer**, retain the Submission ID and wait for final determination.

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
- [x] PREP Active `Protect main` ruleset blocks deletion/non-fast-forward updates; private vulnerability reporting enabled.

### SignPath Foundation plan

Adopted project sequence:

`clean public repo → prerequisite public release → SignPath Foundation application → GitHub origin verification/signing integration → signed candidate → Defender/SmartScreen + Windows validation → final release update`

The prerequisite public-release step is complete. Do not invent `.signpath/policies/...` identifiers before SignPath supplies the actual project/signing-policy slugs.

All jobs leading to the intended signing request remain on GitHub-hosted runners, and the workflow uploads the Windows artifact before release publication so it can later be handed to the SignPath signing request with origin verification.

## Release-candidate sign-off record

- **Public source/privacy audit:** PASS
- **Public Git commit identity:** PASS (`noreply`)
- **Hotfix regression:** PASS — run `33258276374`
- **Fixed Windows candidate pipeline:** PASS — run `33258556273`
- **External 1920×1080 portability validation:** PASS
- **Full-view UI:** PASS
- **Compact UI:** PASS
- **Scrollbars:** PASS
- **Portable art overrides:** PASS
- **Replay responsiveness/presentation:** PASS
- **Vanilla live functional tests:** PASS
- **Fresh Reset Run / earnings rerun:** PASS
- **String-mod representative tests:** PASS
- **Bugsy/Carlos five-rule reconciliation:** PASS
- **Public prerequisite release:** PASS — `v0.6.0`
- **Defender affected-file provenance:** PASS — exact official EXE hash confirmed
- **Microsoft Defender false-positive dispute/final determination:** PENDING
- **SignPath acceptance/integration:** PENDING
- **Signed Windows Defender/SmartScreen validation:** PENDING
- **Final post-signing release-head regression:** PENDING
