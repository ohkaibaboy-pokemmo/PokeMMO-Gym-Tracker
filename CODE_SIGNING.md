# Code signing policy

PokeMMO Gym Cooldown Tracker is an open-source project distributed under the MIT License.

Free code signing provided by SignPath.io, certificate by SignPath Foundation.

## Project and repository

- Source repository: `https://github.com/ohkaibaboy-pokemmo/PokeMMO-Gym-Tracker`
- License: MIT
- Maintainer: `ohkaibaboy-pokemmo` / OhKaibaBoy

Only artifacts built from this project's own reviewed source repository and build configuration may be submitted for signing.

## Roles

This is currently a single-maintainer project.

- Committer: OhKaibaBoy (`ohkaibaboy-pokemmo`)
- Reviewer: OhKaibaBoy (`ohkaibaboy-pokemmo`)
- Release/signing approver: OhKaibaBoy (`ohkaibaboy-pokemmo`)

If additional maintainers are added, these roles will be updated before they participate in release signing.

## Release signing

Release signing is intended to use SignPath's trusted GitHub build integration and origin verification. Signed release artifacts must be traceable to the public repository, exact commit and GitHub Actions build that produced them.

Every release signing request requires manual approval. Signing is reserved for release artifacts; ordinary development and validation artifacts are not release-signed.

## Artifact identity

Signed Windows executables must use consistent project metadata, including the project name and release version. Upstream or third-party binaries are not to be re-signed as if they were produced by this project.

## Privacy policy

This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.

The tracker reads locally written PokeMMO `chat_*.log` files and stores its own state locally. Users should review logs before sharing them because PokeMMO logs may contain chat, usernames, whispers and other private conversation data.

## Security and user control

The application does not inject into PokeMMO, read process memory, hook functions, inspect or modify game traffic, automate input, or modify the PokeMMO client.

The project will follow SignPath Foundation's open-source signing conditions, including repository/build provenance requirements, GitHub-hosted build requirements for the signing path, manual signing approval, and multi-factor authentication requirements for source-control and signing access.
