# Security Policy

## Supported versions

Security fixes are applied to the current supported release and the active release candidate on `main`.

## Reporting a vulnerability

Please do **not** publish security-sensitive details, private PokeMMO chat content, usernames, whispers, local file paths, or raw `chat_*.log` files in a public issue.

When GitHub private vulnerability reporting is available for this repository, use that channel for security reports. If it is not available, open a minimal issue titled **Security contact request** without vulnerability details or private data so a private reporting channel can be arranged.

For ordinary bugs that do not contain sensitive information, use the normal GitHub issue tracker.

## Project security boundary

PokeMMO Gym Cooldown Tracker is designed as a passive local companion. It reads PokeMMO's locally written chat logs and stores tracker state locally. It does not inject into PokeMMO, read process memory, hook functions, inspect or modify network traffic, capture the screen, use OCR, automate input, or modify the game client.

See `CODE_SIGNING.md` for the release-signing and provenance policy.
