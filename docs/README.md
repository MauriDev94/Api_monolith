# Documentation index

> Entry point for everything under `docs/`. Updated 2026-08-25 alongside the
> mypy strict PR (#113) and the harness standard adoption (#111).

## What lives here

`docs/` is the project's living documentation. It contains three kinds of
content: **architecture & ADRs** (current, source-of-truth), **bitácora**
(chronological record of major changes), and **history** (archived
proposals and audits that explain why something WAS built but no longer
is).

## Current layout

```
docs/
├── README.md                                 ← this file
├── ARCHITECTURE.md                           (loose at root — see proposal)
├── REMEDIATION_PROGRESS.md                   (loose at root — see proposal)
├── pr-conventions.md                         (loose at root — see proposal)
├── adr/
│   └── README.md                             how to write an ADR
├── architecture/
│   └── README.md                             module boundaries & dependency rules
├── bitacora/
│   └── monolith-aplicar-estandar.md          record of harness standard adoption (#111, #113)
└── history/
    ├── AUDIT_PRODUCTION_READINESS.md         snapshot of audit findings (pre-remediation)
    ├── PRD_FASE9_EMAIL_NOTIFICATIONS.md      archived PRD (feature deleted in #80)
    ├── SDD_PROPOSAL_PHASE7_NOTIFICATIONS.md  archived proposal (feature deleted in #80)
    └── SDD_PROPOSAL_PHASE10_GOOGLE_SSO.md    archived proposal (feature shipped via #106)
```

### Files loose at the root of `docs/`

Three files live at the root of `docs/` rather than in a thematic
subfolder: `ARCHITECTURE.md`, `REMEDIATION_PROGRESS.md`,
`pr-conventions.md`. They were placed there when the project started and
have accumulated cross-links from the main `README.md` and `roadmap.md`,
so moving them would break those links. See "Proposed reorganization"
below for a path that doesn't break links.

### Files at the root of the repo that intentionally stay untracked

These three files are listed in `.gitignore` as personal study material
and are intentionally NOT part of the repo's documentation. They stay
on each contributor's local working copy only:

- `prd.md` (work-in-progress product spec)
- `prdAuth.md` (auth-specific PRD draft)
- `docs/STUDY_GUIDE.md` (study material)

## Per-file summary

| File | Purpose | Status |
|------|---------|--------|
| `ARCHITECTURE.md` | Full architecture: Clean/DDD layering, feature layout, dependency rules, JWT/auth flow, deployment topology. **Linked from `README.md` line 63 — DO NOT move without updating that link.** | Current, source of truth |
| `REMEDIATION_PROGRESS.md` | Phase-by-phase progress through the production-readiness remediation (Fases 4-11). Tracks which PRs closed which audit findings. **Linked from `roadmap.md`.** | Historical progress log |
| `pr-conventions.md` | Rules for PR bodies: how to fill the template, which sections to include, which to omit. | Operational convention |
| `adr/README.md` | How to author ADRs in this project (numbering, scope, format). The directory itself contains zero ADRs yet — the first one will be `0007-...` since `0001` through `0006` live in the harness repo. | Authoring guide |
| `architecture/README.md` | How to document module boundaries and dependency rules. | Authoring guide |
| `bitacora/monolith-aplicar-estandar.md` | Chronological record of the harness standard adoption: what landed in PR #111 (adoption) and PR #113 (mypy strict + 42 fixes). Feeds `harness sync --check`. | Current |
| `history/AUDIT_PRODUCTION_READINESS.md` | The original 4-block audit that triggered the remediation. Snapshot of findings as found, before fixes. | Archived (immutable) |
| `history/PRD_FASE9_EMAIL_NOTIFICATIONS.md` | PRD for the email notifications feature (TODO reminders). The feature itself was deleted in PR #80 (dead code / YAGNI). Kept as design history. | Archived (immutable) |
| `history/SDD_PROPOSAL_PHASE7_NOTIFICATIONS.md` | SDD proposal for the same deleted feature. | Archived (immutable) |
| `history/SDD_PROPOSAL_PHASE10_GOOGLE_SSO.md` | SDD proposal for Google SSO login. Feature was shipped (PR #106). Kept for traceability of the design decisions. | Archived (immutable) |

## Proposed reorganization

> **Status: PROPOSAL — NOT APPLIED.** Applying this would require
> updating cross-links in `README.md`, `roadmap.md`,
> `docs/ARCHITECTURE.md`, and `contributing.md`. It is intentionally NOT
> done in this PR to keep the diff focused. Tabled for a future
> docs-only PR.

```
docs/
├── README.md
├── architecture/                  ← new home for ARCHITECTURE.md
│   ├── README.md                  (already here)
│   └── ARCHITECTURE.md            ← move from root
├── process/                       ← new home for pr-conventions.md
│   └── pr-conventions.md          ← move from root
├── history/                       (split into typed subdirs)
│   ├── audits/
│   │   └── AUDIT_PRODUCTION_READINESS.md
│   ├── proposals/
│   │   ├── PRD_FASE9_EMAIL_NOTIFICATIONS.md
│   │   ├── SDD_PROPOSAL_PHASE7_NOTIFICATIONS.md
│   │   └── SDD_PROPOSAL_PHASE10_GOOGLE_SSO.md
│   └── remediation/
│       └── REMEDIATION_PROGRESS.md    ← move from root
├── adr/
│   └── README.md
├── bitacora/
│   └── monolith-aplicar-estandar.md
└── (loose files: none)
```

### Why this proposal, and what's blocking it

- **Groups by audience**: `architecture/` is read at onboarding,
  `process/` is read before opening a PR, `history/` is referenced
  from `roadmap.md` but rarely read end-to-end.
- **Splits `history/`** into `audits/` and `proposals/` so the
  archived content is browsable by type.
- **`REMEDIATION_PROGRESS.md` is a process log**, not architecture —
  belongs in `history/remediation/`.
- **Blocked by cross-links**: `README.md:63` and `README_ES.md:63`
  link directly to `docs/ARCHITECTURE.md`; `roadmap.md` references
  `docs/REMEDIATION_PROGRESS.md` and several paths under
  `docs/history/`. Moving requires a follow-up PR to update all of
  them, plus a search-and-replace in any third-party docs.

## Conventions for new docs

- Architecture / module-boundary docs → `docs/architecture/`
- Process / how-we-work docs → `docs/process/`
- Major-change chronologies → `docs/bitacora/YYYY-MM-slug.md`
- ADRs → `docs/adr/NNNN-slug.md` (see `docs/adr/README.md`)
- Anything obsolete / superseded → `docs/history/`, never deleted
