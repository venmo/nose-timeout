import sys
import logging
import signal
import threading
import traceback

from nose.plugins.base import Plugin
from backports.shutil_get_terminal_size import get_terminal_size

logger = logging.getLogger('nose.plugins.nose_timeout')


class TimeoutException(Exception):
    message = "Stopped by timeout"


class NoseTimeout(Plugin):
    """
    Abort long-running tests
    """
    name = 'timeout'

    def __init__(self):
        Plugin.__init__(self)
        self.timeout = 0

    def options(self, parser, env):
        parser.add_option(
            "--timeout",
            action="store",
            dest="timeout",
            default=env.get('NOSE_TIMEOUT', 0),
            help=(
                "When reach this timeout the test is aborted"
            ),
        )

    def configure(self, options, config):
        self.timeout = options.timeout
        if not self._options_are_valid():
            self.enabled = False
            return

        self.enabled = True

    def _options_are_valid(self):
        try:
            self.timeout = int(self.timeout)
        except ValueError:
            logger.critical("--timeout must be an integer")
            return False

        self.timeout = int(self.timeout)
        if self.timeout < 0:
            logger.critical("--timeout must be greater or equal than 0")
            return False
        return True

    def prepareTestCase(self, test):
        test_timeout = getattr(getattr(test.test, test.test._testMethodName), 'timeout', self.timeout)
        if test_timeout:
            def timeout(result):
                def __handler(signum, frame):
                    dump_stacks()
                    msg = "Function execution is longer than %s second(s). Aborted." % test_timeout
                    raise TimeoutException(msg)

                sig_handler = signal.signal(signal.SIGALRM, __handler)
                signal.alarm(test_timeout)
                try:
                    test.test(result)
                except TimeoutException as e:
                    print(e.message + " timeout")

                finally:
                    signal.signal(signal.SIGALRM, sig_handler)
                    signal.alarm(0)
            return timeout


def dump_stacks():
    """Dump the stacks of all threads except the current thread"""
    current_ident = threading.current_thread().ident
    for thread_ident, frame in sys._current_frames().items():
        if thread_ident == current_ident:
            continue
        for t in threading.enumerate():
            if t.ident == thread_ident:
                thread_name = t.name
                break
        else:
            thread_name = '<unknown>'
        write_title('Stack of %s (%s)' % (thread_name, thread_ident))
        write(''.join(traceback.format_stack(frame)))


def write_title(title, stream=None, sep='~'):
    """Write a section title

    If *stream* is None sys.stderr will be used, *sep* is used to
    draw the line.
    """
    if stream is None:
        stream = sys.stdout
    width, _ = get_terminal_size()
    fill = int((width - len(title) - 2) / 2)
    line = ' '.join([sep * fill, title, sep * fill])
    if len(line) < width:
        line += sep * (width - len(line))
    stream.write('\n' + line + '\n')


def write(text, stream=None):
    """Write text to stream

    Pretty stupid really, only here for symetry with .write_title().
    """
    if stream is None:
        stream = sys.stdout
    stream.write(text)
