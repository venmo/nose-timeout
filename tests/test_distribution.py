
import inspect
import os
import unittest
from optparse import OptionParser

from nose.config import Config
from nose.plugins import PluginTester

from distributed_nose.plugin import DistributedNose

from tests.dummy_tests import TC1, TC2, test_func1, test_func2


class TestTestSelection(unittest.TestCase):

    def setUp(self):
        self.plugin = DistributedNose()
        self.parser = OptionParser()

    def test_nontest_collection(self):
        plug = self.plugin
        plug.options(self.parser, env={})
        args = []
        options, _ = self.parser.parse_args(args)
        plug.configure(options, Config())

        # This is a contrived example; in practice, this can be triggered by
        # function proxies like wrapt.
        nontest = list()
        self.assertEqual(plug.validateName(nontest), None)

    def test_some_tests_found(self):
        # At least some tests should be located
        plug = self.plugin
        plug.options(self.parser, env={})
        args = ['--nodes=2', '--node-number=1']
        options, _ = self.parser.parse_args(args)
        plug.configure(options, Config())

        any_allowed = False

        for test in [TC1, TC2, test_func1, test_func2]:
            if plug.validateName(test) is None:
                any_allowed = True

        self.assertTrue(any_allowed)

    def test_not_all_tests_found(self):
        # But we shouldn't have run all of the tests
        plug = self.plugin
        plug.options(self.parser, env={})
        args = ['--nodes=2', '--node-number=1']
        options, _ = self.parser.parse_args(args)
        plug.configure(options, Config())

        all_allowed = True

        for test in [TC1, TC2, test_func1, test_func2]:
            if plug.validateName(test) is None:
                all_allowed = False

        self.assertFalse(all_allowed)


class TestDistributionBase(unittest.TestCase):
    def _tests_run(self):
        test_lines = str(self.output).split('\n\n')[0].split('\n')
        return [line.split(' ... ')[0] for line in test_lines]


class TestClassDistribution(PluginTester, TestDistributionBase):
    plugins = [DistributedNose()]
    suitepath = 'tests.dummy_tests'
    activate = '--nodes=3'
    args = [
        '--node-number=1',
        '-v',
        # get test names into output
    ]


class TestClassDistributionOff(TestClassDistribution):
    def test_tc1_hashes_apart(self):
        testnames = self._tests_run()
        from_tc1 = [name for name in testnames if '.TC1)' in name]
        self.assertTrue(0 < len(from_tc1) < 4)

    def test_tc3_hashes_apart(self):
        testnames = self._tests_run()
        from_tc3 = [name for name in testnames if '.TC3)' in name]
        self.assertTrue(0 < len(from_tc3) < 5)

    def test_func1_excluded(self):
        self.assertTrue('tests.dummy_tests.test_func1' not in self._tests_run())

    def test_func2_included(self):
        self.assertTrue('tests.dummy_tests.test_func2' in self._tests_run())


class TestClassDistributionOn(TestClassDistribution):
    args = TestClassDistributionOff.args + ['--hash-by-class']

    def test_tc1_is_excluded(self):
        testnames = self._tests_run()
        from_tc1 = [name for name in testnames if '.TC1)' in name]
        self.assertTrue(len(from_tc1) == 0)

    def test_tc3_is_included(self):
        testnames = self._tests_run()
        from_tc3 = [name for name in testnames if '.TC3)' in name]
        self.assertTrue(len(from_tc3) == 5)

    # Function selection should not have changed.
    def test_func1_excluded(self):
        self.assertTrue('tests.dummy_tests.test_func1' not in self._tests_run())

    def test_func2_included(self):
        self.assertTrue('tests.dummy_tests.test_func2' in self._tests_run())


class TestLptDistribution(PluginTester, TestDistributionBase):
    plugins = [DistributedNose()]
    suitepath = 'tests.dummy_tests'
    activate = '--nodes=3'
    args = [
        '--algorithm=least-processing-time',
        '-v'  # get test names into output
    ]
    lpt_all_filepath = os.path.join(
        os.path.dirname(__file__),
        'lpt_data',
        'lpt_all.json'
    )
    lpt_partial_filepath = os.path.join(
        os.path.dirname(__file__),
        'lpt_data',
        'lpt_partial.json'
    )


class TestLptDistributionAllNodeOne(TestLptDistribution):
    args = TestLptDistribution.args + [
        '--node-number=1',
        '--lpt-data={}'.format(TestLptDistribution.lpt_all_filepath),
        '--hash-by-class'
    ]

    def test_only_largest_included(self):
        # The dummy duration data in 'lpt_all.json' is designed
        # such that the first two nodes (of three) should get
        # exactly one class each. The first node should get the
        # longest duration class, which is TC5.

        self.assertEqual(
            self.plugins[0].algorithm,
            DistributedNose.ALGORITHM_LEAST_PROCESSING_TIME
        )

        classes = set(
            name.split('.')[-1][:-1]
            for name in self._tests_run()
            if '.TC' in name
        )

        self.assertTrue(len(classes) == 1)
        # TODO: make compatible with python 2.6 ?
        self.assertIn('TC5', classes)

    # Function selection should not have changed.
    def test_func1_excluded(self):
        self.assertTrue('tests.dummy_tests.test_func1' not in self._tests_run())

    def test_func2_included(self):
        self.assertTrue('tests.dummy_tests.test_func2' in self._tests_run())


class TestLptDistributionAllNodeThree(TestLptDistribution):
    args = TestLptDistribution.args + [
        '--node-number=3',
        '--lpt-data={}'.format(TestLptDistribution.lpt_all_filepath),
        '--hash-by-class'
    ]

    def test_all_smallest_included(self):
        # The dummy duration data in 'lpt_all.json' is designed
        # such that the third node (of three) should get all the
        # short duration tests, namely TC1, TC2, TC4, and TC6.

        self.assertEqual(
            self.plugins[0].algorithm,
            DistributedNose.ALGORITHM_LEAST_PROCESSING_TIME
        )

        classes = set(
            name.split('.')[-1][:-1]
            for name in self._tests_run()
            if '.TC' in name
        )

        self.assertTrue(
            all(
                map(
                    lambda c: c in classes,
                    ['TC1', 'TC2', 'TC4', 'TC6']
                )
            )
        )


class TestLptDistributionPartial(TestLptDistribution):
    # Tests the case where a class is missing from the lpt data file.

    args = TestLptDistribution.args + [
        '--node-number=1',
        '--lpt-data={}'.format(TestLptDistribution.lpt_partial_filepath),
        '--hash-by-class'
    ]

    def test_tc3_is_included(self):
        # The dummy duration data in 'lpt_partial.json' omits TC3,
        # so it should hash to node 1 as in the class distribution tests.
        self.assertEqual(
            self.plugins[0].algorithm,
            DistributedNose.ALGORITHM_LEAST_PROCESSING_TIME
        )

        testnames = self._tests_run()
        from_tc3 = [name for name in testnames if '.TC3)' in name]
        self.assertTrue(len(from_tc3) == 5)
