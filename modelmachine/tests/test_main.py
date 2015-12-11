# -*- coding: utf-8 -*-

"""Test case for cli part of modelmachine package."""

from modelmachine.__main__ import main, VERSION
from pytest import raises

def test_version(tmpdir):
    """Test that it's print current version."""
    output_path = tmpdir.join('output.txt')

    with open(str(output_path), 'w') as stdout:
        main(['modelmachine', '--version'], stdout)

    assert output_path.read() == 'ModelMachine ' + VERSION + '\n'

    with open(str(output_path), 'w') as stdout:
        main(['modelmachine', '-v'], stdout)

    assert output_path.read() == 'ModelMachine ' + VERSION + '\n'

def test_usage(tmpdir):
    """Test that it's print usage."""
    output_path = tmpdir.join('output.txt')

    with open(str(output_path), 'w') as stdout:
        main(['modelmachine', '--help'], stdout)
    assert output_path.read().startswith('usage:')

    # TODO: Add stderr capture
    # with open(str(output_path), 'w') as stdout:
    #     with raises(SystemExit):
    #         main(['modelmachine', 'wrong_command'], stdout)
    # assert output_path.read().startswith('usage:')
