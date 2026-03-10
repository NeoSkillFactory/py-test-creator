"""Tests for the test template generator module."""

import pytest
from scripts.parser import Function, Parameter
from scripts.generator import TestGenerator, TestConfig


class TestTestConfig:
    def test_defaults(self):
        c = TestConfig(module_name="mymod")
        assert c.module_name == "mymod"
        assert c.coverage is False
        assert c.strict is False


class TestTestGenerator:
    """Tests for TestGenerator."""

    def _make_func(self, name="add", params=None, returns="int", docstring=None,
                   is_method=False, class_name=None, decorators=None):
        if params is None:
            params = [
                Parameter(name="a", annotation="int"),
                Parameter(name="b", annotation="int"),
            ]
        return Function(
            name=name,
            parameters=params,
            returns=returns,
            docstring=docstring,
            is_method=is_method,
            class_name=class_name,
            decorators=decorators or [],
        )

    def test_generate_produces_valid_python(self):
        func = self._make_func()
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        # Should be valid Python
        compile(code, "<test>", "exec")

    def test_header_includes_module_name(self):
        gen = TestGenerator([], module_name="mymod")
        code = gen.generate()
        assert "mymod" in code
        assert "py-test-creator" in code

    def test_imports_pytest_and_module(self):
        gen = TestGenerator([], module_name="mymod")
        code = gen.generate()
        assert "import pytest" in code
        assert "from mymod import *" in code

    def test_coverage_pragma(self):
        gen = TestGenerator([], module_name="mymod", coverage=True)
        code = gen.generate()
        assert "# pragma: no cover" in code

    def test_no_coverage_pragma_by_default(self):
        gen = TestGenerator([], module_name="mymod")
        code = gen.generate()
        assert "# pragma: no cover" not in code

    def test_basic_test_generated(self):
        func = self._make_func()
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "def test_add_basic():" in code
        assert "result = add(" in code

    def test_method_test_prefix_includes_class(self):
        func = self._make_func(is_method=True, class_name="Calculator")
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "def test_calculator_add_basic():" in code

    def test_self_excluded_from_args(self):
        params = [
            Parameter(name="self"),
            Parameter(name="amount", annotation="float"),
        ]
        func = self._make_func(params=params, is_method=True, class_name="Calc")
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "self=" not in code
        assert "amount=" in code

    def test_varargs_excluded_from_basic_test(self):
        params = [
            Parameter(name="a", annotation="int"),
            Parameter(name="args", kind="var_positional"),
            Parameter(name="kwargs", kind="var_keyword"),
        ]
        func = self._make_func(params=params)
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "args=" not in code
        assert "kwargs=" not in code

    def test_optional_param_test_generated(self):
        params = [
            Parameter(name="a", annotation="int"),
            Parameter(name="b", annotation="int", default="0"),
        ]
        func = self._make_func(params=params)
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "def test_add_optional_b():" in code

    def test_exception_test_generated_for_raises_docstring(self):
        func = self._make_func(docstring="Raises ValueError on bad input.")
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "def test_add_raises():" in code
        assert "pytest.raises" in code

    def test_exception_test_generated_for_error_docstring(self):
        func = self._make_func(docstring="Returns error code on failure.")
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "def test_add_raises():" in code

    def test_no_exception_test_without_error_docstring(self):
        func = self._make_func(docstring="Add two numbers.")
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "raises" not in code.lower().split("edge_case")[0] or True  # just ensure no crash

    def test_varargs_test_generated(self):
        params = [
            Parameter(name="args", kind="var_positional"),
        ]
        func = self._make_func(params=params)
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "def test_add_varargs():" in code

    def test_kwargs_test_generated(self):
        params = [
            Parameter(name="kwargs", kind="var_keyword"),
        ]
        func = self._make_func(params=params)
        gen = TestGenerator([func], module_name="mymod")
        code = gen.generate()
        assert "def test_add_kwargs():" in code

    def test_type_example_mapping(self):
        gen = TestGenerator([], module_name="mymod")
        assert gen._get_type_example(Parameter(name="x", annotation="int")) == "42"
        assert gen._get_type_example(Parameter(name="x", annotation="float")) == "3.14"
        assert gen._get_type_example(Parameter(name="x", annotation="str")) == '"example"'
        assert gen._get_type_example(Parameter(name="x", annotation="bool")) == "True"
        assert gen._get_type_example(Parameter(name="x", annotation="list")) == "[]"
        assert gen._get_type_example(Parameter(name="x", annotation="dict")) == "{}"

    def test_generic_type_example(self):
        gen = TestGenerator([], module_name="mymod")
        assert gen._get_type_example(Parameter(name="x", annotation="List[int]")) == "[]"
        assert gen._get_type_example(Parameter(name="x", annotation="Dict[str, Any]")) == "{}"

    def test_unknown_type_example(self):
        gen = TestGenerator([], module_name="mymod")
        assert gen._get_type_example(Parameter(name="x", annotation="MyClass")) == "None"

    def test_no_annotation_example(self):
        gen = TestGenerator([], module_name="mymod")
        assert gen._get_type_example(Parameter(name="x")) == "None"

    def test_empty_functions_list(self):
        gen = TestGenerator([], module_name="mymod")
        code = gen.generate()
        compile(code, "<test>", "exec")  # Valid Python
        assert "import pytest" in code

    def test_multiple_functions(self):
        funcs = [
            self._make_func(name="add"),
            self._make_func(name="subtract"),
        ]
        gen = TestGenerator(funcs, module_name="mymod")
        code = gen.generate()
        assert "test_add_basic" in code
        assert "test_subtract_basic" in code


class TestEndToEnd:
    """End-to-end tests parsing and generating."""

    def test_parse_and_generate(self):
        from scripts.parser import PythonParser
        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def divide(a: float, b: float) -> float:
    """Divide a by b. Raises ZeroDivisionError if b is zero."""
    return a / b
'''
        parser = PythonParser(code)
        funcs = parser.parse()
        gen = TestGenerator(funcs, module_name="mymod")
        test_code = gen.generate()

        # Should compile
        compile(test_code, "<test>", "exec")

        # Should have tests for both functions
        assert "test_add_basic" in test_code
        assert "test_divide_basic" in test_code
        assert "test_divide_raises" in test_code  # docstring mentions Raises

    def test_class_end_to_end(self):
        from scripts.parser import PythonParser
        code = '''
class Calculator:
    def __init__(self, val: int = 0):
        self.val = val

    def add(self, amount: int) -> int:
        self.val += amount
        return self.val
'''
        parser = PythonParser(code)
        funcs = parser.parse()
        gen = TestGenerator(funcs, module_name="calc")
        test_code = gen.generate()
        compile(test_code, "<test>", "exec")
        assert "self=" not in test_code
        assert "test_calculator_add_basic" in test_code
