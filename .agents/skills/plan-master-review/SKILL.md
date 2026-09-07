---
name: plan-master-review
description: Compare PROJECT_PLAN.md with the latest origin/master, update implementation when the plan or source has meaningful changes, and run the plan dashboard. Use for implementation-progress reviews, plan tracking, or requests to compare the project against master.
---

# Plan and master review

Use this workflow for this project whenever implementation progress is being reviewed.

The tracked `plan_dashboard.py` is only the stable entry point. The actual analysis, findings, and Streamlit UI/UX must be generated into the untracked `plan_dashboard_generated.py` file during this workflow. Do not hardcode plan-specific findings or UI into the entry point.

## 1. Establish the remote baseline

Run from the repository root:

```bash
git fetch origin master
```

Use `origin/master` as the remote reference. Do not run `git pull`, `git checkout`, `git reset`, or overwrite the user's working tree automatically.

If fetch fails, stop the comparison, report the error, and do not present stale remote data as current.

## 2. Compare the plan and source

Read:

- `PROJECT_PLAN.md` from `origin/master` when available
- the current project source and tests
- recent `origin/master` commits
- `git diff master..origin/master --stat` and relevant file diffs

Determine whether the remote change affects the plan, implementation, tests, configuration, or dashboard analysis. Do not treat a commit-count change alone as proof that implementation work is required.

### 2.1 Evidence-based item scoring

Do not calculate completion by counting plan words found anywhere in the repository. Generic words such as `구현`, `표시`, `수집`, and `화면` are not evidence of a completed feature.

For every plan bullet, record concrete evidence at the item level:

- implementation evidence: the relevant source file and behavior;
- test evidence: a focused automated test, when the repository has tests;
- documentation or configuration evidence, when the item requires it;
- missing evidence and the next verification needed.

A plan item is `완료` only when its required implementation behavior is demonstrated by source and, where applicable, tests or a runnable configuration. A matching filename or keyword alone is insufficient. Mark items `부분 완료` when only some sub-requirements are evidenced, and `미구현` or `미확인` when no reliable evidence exists. Calculate phase and overall progress from these item judgments, not from raw keyword overlap. Keep the evidence and missing checks visible in the generated dashboard.

## 3. Decide what to do

### No meaningful implementation change

If the plan and implementation remain aligned, reuse or regenerate `plan_dashboard_generated.py` from the current `origin/master` evidence, do not modify the stable entry point, and run the dashboard:

```bash
docker compose up --build
```

For this repository, use the default dashboard service and report the URL `http://localhost:8502` and the remote commit used for analysis.

### Meaningful change detected

If the plan or remote implementation changes, analyze the remote source and update the smallest relevant project source, tests, or generated dashboard module needed to keep the project aligned. Regenerate `plan_dashboard_generated.py` with the new findings and UI/UX. Do not blindly rewrite code for every remote commit.

Then run, as applicable:

```bash
docker compose --profile test run --rm test
docker compose up --build
```

Report changed files, the implementation decision, test results, and the dashboard URL.

## 3.1 Final UI/UX verification

Do not treat a successful container start or health check as proof that the dashboard is complete. After the generated dashboard is running, inspect the rendered page in a browser or with an available screenshot/visual inspection tool.

Verify at minimum:

- chart labels are readable and do not overlap, clip, rotate into unreadable text, or disappear;
- chart orientation and sorting make progress comparisons easy to understand;
- metric cards, tables, expanders, and columns align at the target viewport width;
- long Korean and English labels remain understandable on narrow screens;
- empty, partial, error, and loading states have useful messages;
- the displayed status and progress are consistent with the evidence shown below them.

If visual inspection finds a problem, modify or regenerate `plan_dashboard_generated.py`, rebuild the dashboard, and inspect it again. Prefer horizontal bars, shortened display labels with full tooltips/details, or a table when categorical chart labels are too long. Report the final visual check and any remaining limitation; never report completion based only on a healthy server.

## 4. Dashboard truthfulness

- The dashboard must identify the exact `origin/master` commit it analyzed.
- Distinguish remote changes from uncommitted local changes.
- If a plan item cannot be proven from source or tests, mark it partial or unknown rather than complete.
- The generated module must expose `render()` and must be importable by `plan_dashboard.py`.
- The generated module must not contain API keys or credentials and should be treated as a disposable build artifact.
- UI/UX review must be completed after generation and after any generated UI change.
- Keep source links, fallback behavior, UTC/timezone handling, and non-investment-advice wording intact.

## 5. Safety

- Never place API keys or local secrets in source, logs, reports, or Git.
- Preserve unrelated user changes.
- Do not claim that an LLM performed the review unless an LLM agent was actually invoked and its output was validated against repository evidence.
