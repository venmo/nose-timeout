
import os
import unittest
from optparse import OptionParser

from nose.config import Config

from distributed_nose.plugin import DistributedNose


class TestOptionValidation(unittest.TestCase):

    def setUp(self):
        self.plugin = DistributedNose()
        self.parser = OptionParser()

    def test_defaults(self):
        self.plugin.options(self.parser, env={})
        args = []
        options, _ = self.parser.parse_args(args)

        self.assertEqual(options.distributed_node_number, 1)
        self.assertEqual(options.distributed_nodes, 1)
        self.assertEqual(options.distributed_hash_by_class, False)

    def test_vanilla(self):
        self.plugin.options(self.parser, env={})
        args = ['--nodes=4', '--node-number=3']
        options, _ = self.parser.parse_args(args)
        self.plugin.configure(options, Config())

        self.assertEqual(self.plugin.node_count, 4)
        self.assertEqual(self.plugin.node_id, 3)
        self.assertEqual(self.plugin.hash_by_class, False)
        self.assertTrue(self.plugin.enabled)

    def test_env_configs(self):
        env = {'NOSE_NODES': 6,
               'NOSE_NODE_NUMBER': 4,
               'NOSE_HASH_BY_CLASS': 'yes'}
        self.plugin.options(self.parser, env=env)
        options, _ = self.parser.parse_args([])
        self.plugin.configure(options, Config())

        self.assertEqual(self.plugin.node_count, 6)
        self.assertEqual(self.plugin.node_id, 4)
        self.assertEqual(self.plugin.hash_by_class, True)
        self.assertTrue(self.plugin.enabled)

    def test_hash_by_class_via_flag(self):
        env = {'NOSE_NODES': 6,
               'NOSE_NODE_NUMBER': 4}
        self.plugin.options(self.parser, env=env)
        args = ['--hash-by-class']
        options, _ = self.parser.parse_args(args)
        self.plugin.configure(options, Config())

        self.assertEqual(self.plugin.hash_by_class, True)
        self.assertTrue(self.plugin.enabled)

    def test_disable_via_flag(self):
        env = {'NOSE_NODES': 6, 'NOSE_NODE_NUMBER': 4}
        self.plugin.options(self.parser, env=env)
        args = ['--distributed-disabled']
        options, _ = self.parser.parse_args(args)
        self.plugin.configure(options, Config())

        self.assertFalse(self.plugin.enabled)

    def test_integer_required_count(self):
        self.plugin.options(self.parser, env={})
        args = ['--nodes=foo', '--node-number=1']
        options, _ = self.parser.parse_args(args)
        self.plugin.configure(options, Config())

        self.assertFalse(self.plugin.enabled)

    def test_integer_required_id(self):
        self.plugin.options(self.parser, env={})
        args = ['--nodes=2', '--node-number=baz']
        options, _ = self.parser.parse_args(args)
        self.plugin.configure(options, Config())

        self.assertFalse(self.plugin.enabled)

    def test_id_in_range(self):
        self.plugin.options(self.parser, env={})
        args = ['--nodes=2', '--node-number=3']
        options, _ = self.parser.parse_args(args)
        self.plugin.configure(options, Config())

        self.assertFalse(self.plugin.enabled)

    def test_lpt_via_flag(self):
        LPT_DATA_FILEPATH = os.path.join(
            os.path.dirname(__file__),
            'lpt_data',
            'lpt_all.json'
        )
        env = {'NOSE_NODES': 6,
               'NOSE_NODE_NUMBER': 4}
        self.plugin.options(self.parser, env=env)
        args = [
            '--algorithm=least-processing-time',
            '--lpt-data={}'.format(LPT_DATA_FILEPATH),
            '--hash-by-class'
        ]
        options, _ = self.parser.parse_args(args)
        self.plugin.configure(options, Config())

        self.assertEqual(
            self.plugin.algorithm,
            DistributedNose.ALGORITHM_LEAST_PROCESSING_TIME
        )
        self.assertTrue(self.plugin.enabled)

    def test_lpt_no_data_arg_aborts(self):
        env = {'NOSE_NODES': 6,
               'NOSE_NODE_NUMBER': 4}
        self.plugin.options(self.parser, env=env)
        args = [
            '--algorithm=least-processing-time'
        ]
        options, _ = self.parser.parse_args(args)

        # TODO: make compatible with python 2.6 ?
        with self.assertRaises(AssertionError):
            self.plugin.configure(options, Config())

    def test_lpt_missing_data_file_aborts(self):
        LPT_DATA_FILEPATH = os.path.join(
            os.path.dirname(__file__),
            'no_such_file.json'
        )
        env = {'NOSE_NODES': 6,
               'NOSE_NODE_NUMBER': 4}
        self.plugin.options(self.parser, env=env)
        args = [
            '--algorithm=least-processing-time',
            '--lpt-data={}'.format(LPT_DATA_FILEPATH)
        ]
        options, _ = self.parser.parse_args(args)

        # TODO: make compatible with python 2.6 ?
        with self.assertRaises(IOError):
            self.plugin.configure(options, Config())

    def test_lpt_invalid_json_file_aborts(self):
        LPT_DATA_FILEPATH = os.path.join(
            os.path.dirname(__file__),
            'lpt_data',
            'lpt_invalid_json.json'
        )
        env = {'NOSE_NODES': 6,
               'NOSE_NODE_NUMBER': 4}
        self.plugin.options(self.parser, env=env)
        args = [
            '--algorithm=least-processing-time',
            '--lpt-data={}'.format(LPT_DATA_FILEPATH)
        ]
        options, _ = self.parser.parse_args(args)

        # TODO: make compatible with python 2.6 ?
        with self.assertRaises(ValueError):
            self.plugin.configure(options, Config())

    def test_lpt_invalid_data_format_aborts(self):
        LPT_DATA_FILEPATH = os.path.join(
            os.path.dirname(__file__),
            'lpt_data',
            'lpt_invalid_data.json',
        )
        env = {'NOSE_NODES': 6,
               'NOSE_NODE_NUMBER': 4}
        self.plugin.options(self.parser, env=env)
        args = [
            '--algorithm=least-processing-time',
            '--lpt-data={}'.format(LPT_DATA_FILEPATH),
            '--hash-by-class'
        ]
        options, _ = self.parser.parse_args(args)

        # TODO: make compatible with python 2.6 ?
        with self.assertRaises(KeyError):
            self.plugin.configure(options, Config())
