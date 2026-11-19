# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Markdown-only knowledge base: four illustrated study guides plus exams and labs that are built from them. Nothing gets built, and there is no test suite or linter. Content is read on GitHub/Obsidian/VS Code, so Mermaid diagrams must render there. The git history has an older .NET project (`Acme.BookStore`) that was deleted; the `.gitignore` is a leftover Visual Studio template.

## Layout and how the pieces relate

- `<topic>-foundations-to-advanced/` for `docker`, `kafka`, `kubernetes` and `rabbitmq`. Each guide has a `README.md` (Mermaid learning path + chapters table with level badges) and numbered chapters `NN-name.md`. The last chapter of each guide is a cheatsheet.
- `practicals/` is derived from the guides. `practicals/<topic>/exam.md` and `playbook.md` are written **only from what the guide chapters say**, and every exam answer links back to the source chapter (`../../<topic>-foundations-to-advanced/NN-name.md`). If you change a guide's facts or rename or renumber a chapter, update the matching exam answers and playbook links too.
- `practicals/rabbitmq/lab/` is a runnable kit: a 3-node `rabbitmq:4.1-management` compose (project name `rmqlab`) and `rmq.py`, a pika CLI built as the `rmq-cli` image. `practicals/rabbitmq/playbook.md` calls its commands (`exchange`, `queue`, `bind`, `publish`, `consume --idle N`) directly, so a change to the CLI's flags must also be made in the playbook.
- `visuals/` holds generated animated HTML pages (one per illustrated `.md` file, mirroring the repo paths). `visuals/build/build.py` builds them: Mermaid is rendered by the pinned `mmdc` with `/usr/bin/chromium`, and the animation is CSS `@keyframes` in `visuals/assets/visuals.css`. After changing a guide's diagrams or prose, rerun `cd visuals/build && python3 build.py` (`npm install` first). A Mermaid parse error fails the build. The same error would also break the diagram on GitHub, so fix it in the Markdown (for example, `;` inside a message ends the statement).
- `labs/` is a scratch area where the user works through the playbooks. It is not content.

## Writing conventions (match existing files)

- **Chapters:** the title is `# NN · Title <level emoji>`. The next line is prev/next nav links (`[← Prev](..) · [Next: X →](..)`). Section headings start with an emoji (`## 🏃 ...`). The chapter ends with `## ✅ Key Takeaways`. Use Mermaid or ASCII diagrams before prose.
- **Level badges:** 🟢 Beginner, 🟡 Intermediate, 🔴 Advanced.
- **Exams:** 100 points, pass mark 70. Part A is 20 multiple-choice questions (2 pts each), B is 8 short-answer questions (3 pts each), C is 3 fix-the-config or design tasks (6 pts each), D is 3 troubleshooting scenarios (6 pts each). Each answer sits in `<details><summary>Answer</summary>`, ends with `→ [NN](link)`, and ends with a scoring table.
- **Playbook labs:** each lab has Goal → Steps → ✅ Verify → 🧠 Explain → 🧹 Cleanup, often with a 💥 break-it step. Runbooks use Symptom → Triage → Causes → Fix → Prevent.
- **Links:** link to a chapter file rather than to a `#heading` anchor when the heading contains an emoji with a variation selector (e.g. 🏗️), because renderers slug those differently.
- **Commands:** pin image versions (`apache/kafka:4.1.0`, `rabbitmq:4.1-management`, `nginx:1.27-alpine`) and publish ports on `127.0.0.1`. Credentials are lab placeholders (`admin` / `change-me`).
- `.prettierrc` uses 4-space indentation and single quotes.

## Verifying lab content

Docker is available locally, so you can run lab steps to check them. Use a scratch directory and a distinct compose project name (`docker compose -p <name>`), and run `down -v` afterwards. Watch out for two things:

- Wrapping `docker run` in `timeout` leaves the container running. Use the tool's own exit option instead, such as `rmq.py consume --idle N` or Kafka console tools' `--timeout-ms`.
- Kafka console consumers print `TimeoutException` when `--timeout-ms` expires. That is normal.

`kind` and `kubectl` are not installed, so the Kubernetes labs can't be run here.
