import unittest

from shorts_pipeline.audio_peaks import find_loud_peaks


class AudioPeakTests(unittest.TestCase):
    def test_loud_window_found(self):
        levels = [-30.0] * 200
        levels[100] = -15.0
        peaks = find_loud_peaks(levels, window_s=5)
        self.assertEqual([p.start_s for p in peaks], [500.0])
        self.assertGreater(peaks[0].amplitude_ratio, 5)

    def test_leaving_silence_is_not_a_peak(self):
        levels = [-90.0] * 100 + [-40.0] * 100   # quiet speech after dead air
        self.assertEqual(find_loud_peaks(levels, window_s=5, baseline_s=50), [])

    def test_empty(self):
        self.assertEqual(find_loud_peaks([]), [])


if __name__ == "__main__":
    unittest.main()
