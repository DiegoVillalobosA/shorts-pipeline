# Architecture

## End-to-end flow

```mermaid
flowchart LR
    subgraph Discover
        A[Stream VODs & public clips<br/>Twitch / Kick / YouTube] --> B[Download VOD + chat<br/>yt-dlp, TwitchDownloader]
    end
    subgraph Detect
        B --> C1[Chat-activity peaks<br/>chat_peaks.py]
        B --> C2[Loudness peaks<br/>audio_peaks.py]
        C1 & C2 --> D[Candidates +<br/>Whisper transcript + frames]
    end
    subgraph Judge
        D --> E{{Humor gate<br/>humor_judge.py}}
        E -- discard --> X[(dropped)]
        E -- burnt --> T[(TOP backlog)]
    end
    subgraph Build
        E -- pass --> F[Layout 9:16<br/>layout.py]
        F --> G[Karaoke subtitles<br/>karaoke.py]
        G --> H[Sound-effect plan<br/>sfx_plan.py]
        H --> I[ffmpeg render]
    end
    subgraph Verify
        I --> J{{QA gates<br/>qa_gates.py}}
        J -- blocking fail --> F
        J --> K[Claude reviews real frames]
    end
    K --> L[/Human: publish + rate 1-5/]
    L --> M[(results.csv)]
    M -. recalibrate .-> E
```

The loop at the bottom is the point of the whole design: every published Short
produces a human rating and real view/retention numbers, and those flow back
into the judge's weights and the written lessons.

## Why the stages are split this way

| Stage | Done by | Why |
|---|---|---|
| Peak detection | deterministic Python | Cheap, repeatable, testable. Finds *energy*. |
| Humor gate | LLM fills a scorecard, Python scores it | Funniness needs vision + language understanding, but the *decision* must be auditable and recalibratable, so arithmetic stays in code. |
| Layout, subtitles, SFX, render | deterministic Python + ffmpeg | A render is a pure function of a config: re-runnable and diffable. |
| QA gates | deterministic Python | Hard rules never rely on a model's mood. |
| Frame review | LLM looks at real frames | "Looks fine" is only allowed after actually viewing extracted frames. |
| Publish + taste | human | The only irreversible step stays with a person. |

## Where it runs

Heavy work (download, transcription, render) runs on the owner's Mac, because
the cloud sandbox cannot reach Twitch or yt-dlp. Claude threads running in the
cloud drive it through an approved folder or a Remote Control session. Nothing
is installed, published, paid for or deleted without an explicit yes.
