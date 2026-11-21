# Orchestration: Claude as the operator

This project is built and run *with* Claude rather than only *about* it. Script,
code, rules, scheduling, quality review and even the analysis of why a Short did
or did not work are done by Claude threads; the human decides taste and presses
Publish.

## One orchestrator, many short-lived threads

A single coordinator chat talks to the owner and spawns **parallel worker
threads**, one per task (find moments in a VOD, build a clip, review frames,
analyse results). A thread closes when its job is done, and anything worth
keeping is written to shared project memory or to files, so the next thread
starts from state rather than from a long chat history.

An earlier version used two different AI agents coordinating through a message
board and mailbox files. After an audit it was collapsed into this single
orchestrator: fewer moving parts, no hand-offs to lose, and one place where
rules live. The old board is archived with an undo script instead of deleted.

## Rules in layers, not in one giant prompt

A comparison with another team's method showed that the issue was never *how
many* rules there are, but *where they live*. Rules are now layered:

| Layer | Content | Loaded |
|---|---|---|
| 0 | <= 12 lines: permissions, autonomy, quiet hours | always |
| 1 | Task skills (`clips-from-streams`): the workflow plus a lessons file | when the task needs it |
| 2 | Code: preflight, QA gates, sync measurement | when the pipeline runs |
| 3 | Archive: old boards and notes | only to look something up |
| 4 | `STATE.md`: <= 40 lines, what a fresh thread reads first | at thread start |

Every lesson carries its provenance so it can be audited and retired:

* `[OWNER]` the channel owner said so
* `[MEASURED]` our own data
* `[EXTERNAL]` a number from someone else's channel or study
* `[HYPOTHESIS]` Claude's guess, to be tested

A lesson that gets broken twice is promoted to a **blocking gate in code**.
Lessons are moved, never deleted, and reviewed monthly against the data.

## Model tiering

| Work | Model tier |
|---|---|
| Mechanical: renaming, cleaning transcripts, titles/descriptions/tags, running scripts | smallest |
| Production and research: ffmpeg, subtitles, scorecards, verification | mid |
| Original scripts, engine code, music, skills, planning | largest |

Chosen automatically per task; cost and latency matter on a daily schedule.

## Daily scheduled task

A scheduled task runs once a day: look for moments in recent VODs/clips of the
target streamers, score them with the humor gate, build the winner, put the
finished MP4 in a review folder, and send a notification **only** if something
scored high enough. If nothing passes, nothing is made: *0-3 clips per VOD, no
quota*.

Guard rails:

* a `STOP` file in the workspace halts every automation (only the owner removes it)
* no AI turns during configured quiet hours (usage quota)
* publish, spend, install, account/security changes and deletes always need a human yes
* the shared folders of other people are read-only
* no secrets in the repo; API keys live in a local env file outside any synced folder

## Honest reporting rule

Claude may not say a clip "looks good" without having looked at real extracted
frames, must separate what the owner confirmed from what it proposes, and
audio/taste judgement belongs to the humans.
