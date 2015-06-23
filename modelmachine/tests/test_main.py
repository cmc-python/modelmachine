# -*- coding: utf-8 -*-

"""Test case for cli part of modelmachine package."""

from modelmachine.__main__ import main, VERSION, USAGE
from pytest import raises

def test_version(tmpdir):
    """Test that it's print current version."""
    output_path = tmpdir.join('output.txt')

    with open(str(output_path), 'w') as stdout:
        main(['modelmachine', 'version'], None, stdout)

    assert output_path.read() == 'ModelMachine ' + VERSION + '\n'

def test_usage(tmpdir):
    """Test that it's print usage (with exit code 1)."""
    output_path = tmpdir.join('output.txt')

    with open(str(output_path), 'w') as stdout:
        main(['modelmachine', 'help'], None, stdout)
    assert output_path.read() == USAGE + '\n'

    with open(str(output_path), 'w') as stdout:
        with raises(SystemExit):
            main(['modelmachine', 'wrong_command'], None, stdout)
    assert output_path.read() == USAGE + '\n'
