import unittest

from shorts_pipeline.layout import Box, ffmpeg_command, filtergraph


class LayoutTests(unittest.TestCase):
    cam = Box(0, 0, 640, 360)

    def test_stacked_portrait_crop(self):
        g = filtergraph("stacked", self.cam, Box(640, 0, 720, 1080))
        self.assertIn("vstack", g)
        self.assertNotIn("overlay", g)

    def test_wide_game_crop_uses_blurred_backdrop(self):
        g = filtergraph("stacked", self.cam, Box(0, 0, 1920, 1080))
        self.assertIn("gblur", g)
        self.assertIn("overlay", g)

    def test_full_mode_needs_no_boxes(self):
        self.assertIn("[base]", filtergraph("full"))

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            filtergraph("stacked")
        with self.assertRaises(ValueError):
            filtergraph("diagonal")

    def test_command_shape(self):
        cmd = ffmpeg_command("in.mp4", 10, 40, "out.mp4", filtergraph("full"))
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("[v]", cmd)
        self.assertEqual(cmd[-1], "out.mp4")


if __name__ == "__main__":
    unittest.main()
