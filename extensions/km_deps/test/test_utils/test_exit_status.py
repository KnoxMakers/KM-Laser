import unittest
import sys

from ink_extensions import inkex
from ink_extensions_utils.exit_status import run

# python -m unittest discover in top-level package dir

class RunWithExitStatusTestCase(unittest.TestCase):

    def test_no_error(self):
        param = "should be returned"
        result = run(self._good_func, param)
        self.assertEqual(param, result)

    def test_error_no_exit_code(self):
        bad_funcs = [self._bad_func_no_exit_code, self._bad_func_no_exit_code_2,
                     self._bad_func_no_exit_code_3]

        for bad_func in bad_funcs:
            with self.assertRaises(SystemExit) as se_context:
                run(bad_func)

            # assert that the SystemExit exception will cause a non-0 exit status
            self.assertEqual(len(se_context.exception.args), 1)
            self.assertNotEqual(None, se_context.exception.args[0])
            self.assertNotEqual(0, se_context.exception.args[0])
            self.assertIn("It is probable that an error occurred", se_context.exception.args[0])
        
    def test_error_with_exit_code(self):
        param = "should be raised"
        with self.assertRaises(SystemExit) as se_context:
            run(self._bad_func_with_exit_code, param)

        self.assertEqual(param, se_context.exception.args[0])

    def test_integration(self):
        ''' use actual inkex.Effect.affect '''

        AnEffect = inkex.Effect()

        with self.assertRaises(SystemExit) as se_context:
            # using a nonexistent file triggers a sys.exit() from inkex
            run(AnEffect.affect, ["nonexistent.svg"])

        self.assertEqual(len(se_context.exception.args), 1)
        self.assertIn("It is probable that an error occurred", se_context.exception.args[0])
        
    @staticmethod
    def _good_func(retval):
        return retval

    @staticmethod
    def _bad_func_no_exit_code():
        sys.exit()
        return "never used"

    @staticmethod
    def _bad_func_no_exit_code_2():
        exit()
        return "never used"

    @staticmethod
    def _bad_func_no_exit_code_3():
        quit()
        return "never used"

    @staticmethod
    def _bad_func_with_exit_code(exit_message):
        sys.exit(exit_message)
        return "never used"
