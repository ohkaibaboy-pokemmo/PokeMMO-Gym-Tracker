# PokeMMO Gym Cooldown Tracker

An unofficial lightweight Windows companion for tracking PokeMMO Gym Leader rematch cooldowns, the 5-other-trainer requirement, rerun routes, and locally detected rerun earnings from PokeMMO's own `chat_*.log` files.

## What it does

- Detects Gym Leader challenges and confirmed victories from `chat_*.log`.
- Starts an 18-hour cooldown only after a confirmed Gym Leader win.
- Tracks the separate 5-other-trainer rematch requirement.
- Counts detected trainer victories toward active 5-rule requirements by default, with a narrow explicit exclusion list for empirically proven exceptions.
- Keeps cooldown, five-rule and earnings state separated by character.
- Replays historical chat logs to reconstruct cooldowns and backfill payout events.
- Supports built-in and user-created rerun routes with route-order sorting and progress.
- Provides an always-on-top frameless Compact rerun overlay.
- Includes Dark, PokeMMO and Light themes plus original leader-specific pixel portraits and gym-type markers.
- Records actual prize-money lines already written by PokeMMO and provides an offline route/charm earnings calculator.
- Supports explicit UI scaling from 0.85× through 2.0× without changing Tk's global DPI setting.
- Supports portable local type-icon and leader-sprite overrides beside the executable.

## Current milestone — v0.6 public release

The first public Windows release, **v0.6.0**, is available from GitHub Releases. It is intentionally unsigned while the project applies for SignPath Foundation open-source code signing.

This repository is the clean public source repository for v0.6. Its public history begins from an audited source snapshot; the earlier private development repository is retained separately and is not part of this repository's history.

v0.6 redesigns the Full dashboard, improves Compact presentation, adds responsive replay/live-tail handling, separates current-run earnings from route projections, supports portable art overrides, and removes user-facing manual Gym-state mutation.

The tracker is intentionally **log-derived**. Earlier v0.6 manual correction controls were removed after synthetic test events were shown to pollute real five-rule state. Replay is the recovery mechanism for missed live ingestion.

The formal v0.6 validation record is documented in `V060_TEST_PLAN.md`. Runtime/UI validation, the hardened Windows build pipeline, and the public v0.6.0 release workflow have passed. SignPath integration and signed-package validation are the remaining distribution work.

## Dashboard

Full view uses the hierarchy:

**Header/KPIs → Controls → Gym Route → Detector**

Headline cards show **Ready**, **Waiting**, **Cooldown** and **Run Earnings**. A separate **Run Details** card shows route base, actual run earnings, route gyms and other payouts.

Gym Route rows use:

**Portrait → # → Type + Leader → Gym → Region → 5-rule → Cooldown → Last Defeated → Status → Payout**

Compact view is intentionally a rerun overlay rather than a miniature copy of Full view. It keeps the controls and route information needed while playing and remains frameless, draggable and always on top.

## Five-rule and cooldown behaviour

Every detected normal trainer victory counts toward all currently active Gym requirements by default unless that opponent is explicitly excluded by empirical evidence.

A different Gym Leader also counts toward other active Gym requirements. The just-defeated Gym Leader does not count toward its own newly reset requirement. Counts cap at `5/5`.

Cooldown is 18 hours per character:

- active timer → `COOLDOWN`;
- expired timer + fewer than five qualifying battles → `WAITING` / `Need N battle(s)`;
- expired timer + `5/5` → `READY` / `00:00:00`.

PokeMMO's own rematch rejection remains authoritative evidence and is shown as a warning in the Detector.

## Replay and live log handling

The tracker tails the current PokeMMO log without blocking the UI. Stable unterminated end-of-file records are processed after they remain unchanged across polls, while genuinely growing partial records are deferred.

Replay is asynchronous and reconstructs useful battle, victory/Gym and payout history without duplicating persistent state. Replaying the same file replaces the previous Detector replay session instead of stacking duplicate presentation rows.

## Earnings

PokeMMO payout lines such as:

`<character> got $8632 for winning!`

are linked to the preceding confirmed victory and stored as de-duplicated local earnings events.

`Reset Run` starts a fresh accounting window without deleting payout history. Current-run Gym payouts, route progress and ordinary trainer payouts remain separated.

The built-in `6 Pillows — Current 30` route currently has a stored base payout of **$268,632** before charm/Donator effects.

The earnings calculator remains offline. Charm prices are entered manually; the app does not fetch GTL or market prices.

## Portable local art

The packaged Windows layout supports optional overrides beside the executable:

```text
PokeMMO Gym Tracker.exe
custom/
├── type_icons/
└── leader_sprites/
```

Type icons are scoped by type, for example `rock.png`, `water.png` or `electric.png`.

Leader overrides use slugged filenames such as `brock.png`, `misty.png`, `lt_surge.png` and `tate_liza.png`.

Missing or invalid overrides fall back to the built-in original art. No external asset download is performed at runtime.

## Compliance boundary

The tracker is deliberately passive:

`PokeMMO local chat log → tracker parser/state → dashboard`

It does **not** inject into PokeMMO, read process memory, hook functions, inspect or modify game traffic, connect to PokeMMO servers, alter game/client files, capture the screen, use OCR, or automate keyboard/mouse/controller inputs.

The application currently makes **no runtime API calls or other external network requests**.

Vanilla PokeMMO log output is the canonical supported parser format. Third-party string-mod compatibility is best-effort.

## Building

Development requirements:

- Python 3.12+
- Tkinter
- the pinned Windows build toolchain in `requirements-build.txt`

Validate source and run tests:

```powershell
python -m py_compile app/main.pyw
Get-ChildItem app/tracker/*.py | ForEach-Object { python -m py_compile $_.FullName }
python -m unittest discover -s tests -v
```

Install the pinned release build tools and build the standalone executable:

```powershell
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --onefile --windowed --paths app --name "PokeMMO Gym Tracker" app/main.pyw
```

GitHub Actions runs regressions on GitHub-hosted runners and produces deliberate Windows artifacts rather than consuming Windows-hosted minutes on every development commit. Normal users do **not** need Python installed.

## Code signing policy

The project intends to use the SignPath Foundation open-source code-signing programme for public Windows releases.

**Free code signing provided by SignPath.io, certificate by SignPath Foundation.**

See [CODE_SIGNING.md](CODE_SIGNING.md) for the project code signing policy, maintainer roles, privacy statement and release-signing rules.

## Privacy

Do not upload raw PokeMMO logs when reporting issues unless they have been reviewed first. Logs can contain team chat, whispers, usernames and other private conversation data.

The repository intentionally ignores `*.log`, local state/config files, executables and build output. Regression tests use sanitized fictional data.

See [SECURITY.md](SECURITY.md) for security-reporting guidance.

## Status

v0.6.0 is publicly released as an **unsigned** Windows build. The release workflow and package build are green. The project is now applying for SignPath Foundation code signing; after acceptance, a signed candidate will be built and validated before the release is updated with the signed artifact.

The project is unofficial and should not be described as PokeMMO-approved unless PokeMMO staff explicitly approves the software.

## License

MIT. See [LICENSE](LICENSE).
