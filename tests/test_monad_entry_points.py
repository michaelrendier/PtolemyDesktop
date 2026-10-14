"""Every monad that has a speaking entry point must be selectable by the console loader (Phase 42, 2026-10-14).
Run (from PtolemyDesktop/):  .venv/bin/python tests/test_monad_entry_points.py -v"""
import contextlib, io, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "VAPMIP"))
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import ptolemy_console as pc

class _Next:
    kind = "dummy"; enabled = True
    def say(self, t): return ("(next)", {})
    def status(self): return "dummy"

# the twelve voices measured in Phase 42 (module -> expected adapter family)
SPEAKING = ["19D_rotary_boxkite_monad", "scaled_mind_eye_boxkite_kernel_monad", "rotary_rerun_boxkite_monad",
            "monad", "monad_harness_diagnostic", "walkwithme_monad",
            "ptolemy_monad", "VQ_rotary_monad", "rotary_monad", "ZD_rotary_monad",
            "boxkite_orbweaver_monad", "monad_english_io"]

class EntryPoints(unittest.TestCase):
    def test_all_twelve_voices_load_and_answer(self):
        names = set(pc.discover_monads())
        for n in SPEAKING:
            self.assertIn(n, names, n)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                m = pc.load_monad_by_name(n, _Next())
                out = m.say("finger pointer")
            reply = out[0] if isinstance(out, tuple) else out
            self.assertTrue(str(reply).strip(), f"{n}: empty reply")
            self.assertFalse(str(reply).startswith("(monad error"), f"{n}: {reply}")

if __name__ == "__main__":
    unittest.main()
