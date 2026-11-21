import unittest

from shorts_pipeline.qa_gates import GateError, check_probe, check_youtube_title, run_gates
from shorts_pipeline.sfx_plan import Event, plan, target_count


def probe(w=1080, h=1920, dur="30.0", audio=True):
    s = [{"codec_type": "video", "width": w, "height": h}]
    if audio:
        s.append({"codec_type": "audio"})
    return {"streams": s, "format": {"duration": dur, "format_name": "mov,mp4,m4a,3gp,3g2,mj2"}}


class SfxTests(unittest.TestCase):
    def test_spacing_and_unmatched_events(self):
        ev = [Event(1, "title"), Event(2, "punchline"), Event(5, "other"), Event(8, "fail")]
        got = plan(ev, 35)
        self.assertEqual([p.t for p in got], [1, 8])       # 2 s rule + "other" stays silent

    def test_cap(self):
        ev = [Event(3 * i, "punchline") for i in range(1, 12)]
        self.assertEqual(len(plan(ev, 35)), target_count(35)[1])


class QATests(unittest.TestCase):
    def test_good_probe(self):
        self.assertEqual(check_probe(probe(), 30.0), 30.0)

    def test_bad_probes(self):
        for bad, kw in [(probe(w=1920, h=1080), {}), (probe(audio=False), {}),
                        (probe(dur="75"), {}), (probe(dur="31"), {})]:
            with self.assertRaises(GateError):
                check_probe(bad, 30.0)

    def test_titles(self):
        self.assertEqual(check_youtube_title("Streamer finds a huge secret in GTA 6 😳"), [])
        self.assertTrue(check_youtube_title("Too short 😳"))
        self.assertTrue(check_youtube_title("A perfectly fine title without any emoji"))

    def test_gates_block_and_warn(self):
        r = run_gates(probe_data=probe(), expected_duration=30.0, silence_ratio=0.35,
                      youtube_title="Streamer finds a huge secret in GTA 6 😳",
                      onscreen_title="STREAMER BREAKS A CHAIR 💀", first_frame_has_face=False, cuts=5)
        self.assertFalse(r.ok)
        self.assertEqual(len(r.blocking), 1)
        self.assertEqual(len(r.warnings), 2)


if __name__ == "__main__":
    unittest.main()
