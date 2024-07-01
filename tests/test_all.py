import os
import pytest
from pathlib import Path


class_declaration = ("pure_python", "cython")
no_getter = ("skip", "convert")
# output_mod_only = (True, False)


test_path = Path(__file__).parent
base_path = test_path.parent


def test_compilation():
    exit_code = os.system(f"python3 {test_path}/setup.py build_ext --inplace")
    assert exit_code == 0


class TestArgs:
    def test_class_declaration(self, tmp_path):
        test_output = tmp_path / "test_output"
        test_output.mkdir()
        for arg in class_declaration:
            os.system(
                f"python3 {base_path}/converter.py -i {test_path}/input -o {test_output} --class_declaration {arg}"
            )
            good_fp = f"{test_path}/good_outputs/{arg}.py"
            with open(good_fp) as fff:
                good = fff.read()

            output_fp = f"{test_output}/input/trouble.pyx"

            with open(output_fp) as fff:
                for index, line in enumerate(fff.read().splitlines()):
                    assert line == good.splitlines()[index]

    def test_no_getter(self, tmp_path):
        test_output = tmp_path / "test_output"
        test_output.mkdir()
        for arg in no_getter:
            os.system(
                f"python3 {base_path}/converter.py -i {test_path}/input -o {test_output} --no_getter {arg}"
            )
            good_fp = f"{test_path}/good_outputs/{arg}.py"
            with open(good_fp) as fff:
                good = fff.read()

            output_fp = f"{test_output}/input/trouble.pyx"

            with open(output_fp) as fff:
                for index, line in enumerate(fff.read().splitlines()):
                    assert line == good.splitlines()[index]

    def output_mod_only(self): ...
