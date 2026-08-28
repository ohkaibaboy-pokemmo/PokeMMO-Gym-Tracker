# Contributing

Thanks for helping improve PokeMMO Gym Tracker.

## Before opening an issue

- Check that the problem occurs with the current `main` source or latest published release candidate.
- For detection/parser issues, provide the smallest relevant **sanitized** log excerpt possible.
- Remove team chat, whispers, account/character names you do not want public, local file paths and unrelated lines.
- Never upload an unreviewed `chat_*.log` file.

Security-sensitive reports should follow [SECURITY.md](SECURITY.md) rather than being posted publicly.

## Development checks

Use Python 3.12+ and run:

```powershell
python -m py_compile app/main.pyw
Get-ChildItem app/tracker/*.py | ForEach-Object { python -m py_compile $_.FullName }
python -m unittest discover -s tests -v
```

The Windows release toolchain is pinned in `requirements-build.txt`. Do not casually update build-tool versions in release work; validate changes through GitHub Actions.

## Repository hygiene

Do not commit raw PokeMMO logs, local tracker state/configuration, credentials, executables, ZIP artifacts, generated build directories or local user assets.
