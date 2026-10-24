# Contributing to Lucknow Live Events

Thanks for your interest in contributing. This guide explains how to pick up work, open a pull request, and get it merged.

> [!IMPORTANT]
> **All pull requests must target the `develop` branch, not `main`.**
> GitHub selects `main` by default — change the base branch to `develop` before you open the PR.
> `main` only receives releases from `develop`. PRs against `main` will be asked to retarget.

## Ways to contribute

- **Pick up an issue.** Open work is tracked in [issues](https://github.com/LucknowAI/lucknow-live-events/issues) and the [`v1 core flow` milestone](https://github.com/LucknowAI/lucknow-live-events/milestone/1). Issues labelled [`good first issue`](https://github.com/LucknowAI/lucknow-live-events/labels/good%20first%20issue) are a good place to start.
- **Report a bug or suggest a feature.** Open an issue first. Describe what happened, what you expected, and how to reproduce it.
- **Suggest a platform or community.** If a Lucknow tech community publishes events on a platform we don't cover yet, open an issue with a link to its events page.

## Before you start

1. **Claim the issue.** Comment on the issue (e.g. "I'd like to work on this") and wait for a maintainer to assign it to you. Please don't start work on an issue that is already assigned to someone else.
2. **One issue per pull request.** Each PR should solve exactly one issue. If you find something else that needs fixing, open a separate issue.
3. **No issue, no PR.** For anything larger than a typo, open or find an issue first so the approach can be agreed before you write code.

If an assigned issue sees no activity for 7 days, a maintainer may unassign it so someone else can pick it up.

## Workflow

1. **Fork** the repository and clone your fork.
2. **Branch from `develop`:**

   ```bash
   git remote add upstream https://github.com/LucknowAI/lucknow-live-events.git
   git fetch upstream
   git switch -c <type>/<short-description> upstream/develop
   ```

   Example branch names: `feat/bevy-adapter`, `fix/event-date-timezone`, `docs/readme-setup`.

3. **Make your change.** Keep it focused on the issue. One PR should touch one layer (`engine`, `backend`, `frontend`, `db`, `infra` or `docs`) wherever possible.
4. **Run the checks** (see below) and make sure they pass.
5. **Push to your fork** and open a pull request **into `LucknowAI/lucknow-live-events:develop`**.
6. **Fill in the PR template.** Link the issue with `Closes #<number>`.

Keep your branch up to date with `develop` by rebasing, not merging:

```bash
git fetch upstream
git rebase upstream/develop
git push --force-with-lease
```

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <short summary in the imperative mood>
```

| Type | Use for |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or fixing tests |
| `chore` | Tooling, dependencies, build config |

Examples: `feat(engine): add Unstop adapter`, `fix(api): handle events without an end date`.

Keep the summary under 72 characters. Use the body to explain *why* the change was needed.

## Running checks

**Backend** (Python 3.12, from `backend/`):

```bash
ruff check .
ruff format --check .
pytest
```

**Frontend** (from `apps/web/`, using [pnpm](https://pnpm.io/)):

```bash
pnpm install
pnpm lint
pnpm format
pnpm build
```

Please use `pnpm` for all JavaScript dependencies — don't commit a `package-lock.json` or `yarn.lock`.

## Project guidelines

- **Event sources are platform adapters.** Each platform (Bevy, Unstop, Luma, …) has one adapter that reads its public data and maps it to our standard event shape. A new adapter must ship with a saved sample response (fixture) and a test that runs against it, so the test never needs the network.
- **No AI in the core flow.** Fetching, filtering and storing events use plain HTTP and rules. Don't add calls to LLM providers without an issue that has been agreed with the maintainers.
- **Keep it simple.** Prefer the smallest change that solves the issue. Avoid new dependencies unless the issue calls for them.
- **Schema changes** go through an Alembic migration in `backend/alembic/`.

## Security

- **Never commit secrets** — `.env` files, API keys, tokens or passwords. Use `.env.example` to document new variables.
- If you find a security vulnerability, **do not open a public issue**. Contact the maintainers privately through the [LucknowAI](https://github.com/LucknowAI) organisation instead.

## Review

- A maintainer will review your PR. Please respond to feedback by pushing new commits to the same branch.
- The PR title should follow the commit message format above.
- Be patient and kind — everyone here contributes in their own time.
