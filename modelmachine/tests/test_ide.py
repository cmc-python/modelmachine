# -*- coding: utf-8 -*-

"""Test case for IDE."""

from modelmachine.ide import load_source, load_data, store_data, run_file
from modelmachine.cpu import AbstractCPU

from unittest.mock import create_autospec, call
from pytest import raises

def test_load_source():
    """Test load source method."""
    cpu_list = {"mm1": create_autospec(AbstractCPU, True)}

    with raises(ValueError):
        load_source(["[config]", "arch=not_found", "[code]", "00 00", "99 00"],
                    cpu_list)

    config, cpu = load_source(["[config]", "arch=mm1", "key=value",
                               "[code]", "00 00", "99 00"],
                              cpu_list)
    assert config["arch"] == "mm1"
    assert config["key"] == "value"
    cpu.load_source.assert_called_with(["00 00", "99 00"])

    config, cpu = load_source(["[config]\n", "arch=mm1\n", "key=value\n",
                               "[code]\n", "00 00\n", "99 00\n"],
                              cpu_list)
    assert config["arch"] == "mm1"
    assert config["key"] == "value"
    cpu.load_source.assert_called_with(["00 00", "99 00"])

def test_store_data(tmpdir):
    """Test save decimal data function."""
    output_file = tmpdir.join("output.txt")
    cpu = create_autospec(AbstractCPU, True, True)
    cpu.store_dec.return_value = 789
    config = {"output": "100, 101", "output_file": str(output_file)}
    store_data(config, cpu)
    cpu.store_dec.assert_has_calls([call(100), call(101)])
    assert output_file.read() == "789\n789\n"

def test_run_file(tmpdir):
    """Test all run cycle."""
    cpu_list = {"mm1": create_autospec(AbstractCPU, True)}
    cpu_list["mm1"].memory.fetch.return_value = 789
    input_file = tmpdir.join("input.txt")
    input_file.write("123 456")
    output_file = tmpdir.join("output.txt")
    source = ["[config]",
              "arch=mm1",
              "input=100 101",
              "input_file=" + str(input_file),
              "output=102",
              "output_file=" + str(output_file),
              "[code]"
              "00 00",
              "99 00"]
    source_file = tmpdir.join("source.mmach")
    source_file.write("\n".join(source))

    run_file(str(source_file), cpu_list)

    assert output_file.read() == "789"
