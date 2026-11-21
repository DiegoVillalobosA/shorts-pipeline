"""Command line entry point: ``python -m shorts_pipeline <command>``."""
from __future__ import annotations

import argparse
import json
import sys

from . import audio_peaks, chat_peaks, humor_judge, qa_gates


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="shorts_pipeline", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chat-peaks", help="rank chat-activity peaks in a VOD chat JSON")
    c.add_argument("chat_json")
    c.add_argument("--top", type=int, default=10)
    c.add_argument("--window", type=int, default=10)

    a = sub.add_parser("audio-peaks", help="rank loudness peaks in an audio file")
    a.add_argument("audio")
    a.add_argument("--top", type=int, default=8)

    j = sub.add_parser("judge", help="score a humor scorecard (JSON file)")
    j.add_argument("scorecard")

    t = sub.add_parser("check-title", help="validate a YouTube title")
    t.add_argument("title")

    args = p.parse_args(argv)
    if args.cmd == "chat-peaks":
        msgs, covered = chat_peaks.load_chat(args.chat_json)
        if not msgs:
            print("no chat messages found", file=sys.stderr)
            return 1
        for i, pk in enumerate(chat_peaks.detect_peaks(msgs, covered, top=args.top,
                                                       window_s=args.window), 1):
            spam = "  [possible spam]" if chat_peaks.looks_like_spam(pk) else ""
            print(f"{i:2d}. {pk.timestamp}  {pk.messages:4d} msgs  score {pk.score:5.2f}  "
                  f"cut {chat_peaks.hhmmss(pk.cut_from_s)}-{chat_peaks.hhmmss(pk.cut_to_s)}{spam}")
    elif args.cmd == "audio-peaks":
        levels = audio_peaks.measure_levels(args.audio)
        for pk in audio_peaks.find_loud_peaks(levels, top=args.top):
            print(f"{chat_peaks.hhmmss(pk.start_s)}  {pk.level_db} dB  "
                  f"+{pk.db_over_local_median} dB over local median (x{pk.amplitude_ratio})")
    elif args.cmd == "judge":
        card = humor_judge.Scorecard.from_dict(json.load(open(args.scorecard)))
        v = humor_judge.score(card)
        print(json.dumps({"score": v.score, "decision": v.decision.value, "reason": v.reason}))
    elif args.cmd == "check-title":
        problems = qa_gates.check_youtube_title(args.title)
        print("OK" if not problems else "\n".join(problems))
        return 0 if not problems else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
