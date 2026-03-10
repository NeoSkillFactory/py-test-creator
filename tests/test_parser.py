"""Tests for the Python AST parser module."""

import pytest
from scripts.parser import PythonParser, Function, Parameter


class TestParameter:
    """Tests for the Parameter dataclass."""

    def test_required_param(self):
        p = Parameter(name="x", annotation="int")
        assert p.is_required() is True

    def test_optional_param(self):
        p = Parameter(name="x", annotation="int", default="0")
        assert p.is_required() is False

    def test_get_type_hint_with_annotation(self):
        p = Parameter(name="x", annotation="int")
        assert p.get_type_hint() == "int"

    def test_get_type_hint_without_annotation(self):
        p = Parameter(name="x")
        assert p.get_type_hint() == "Any"

    def test_to_dict(self):
        p = Parameter(name="x", annotation="int", default="0", kind="keyword_only")
        d = p.to_dict()
        assert d["name"] == "x"
        assert d["annotation"] == "int"
        assert d["default"] == "0"
        assert d["kind"] == "keyword_only"
        assert d["required"] is False


class TestFunction:
    """Tests for the Function dataclass."""

    def test_get_required_params_excludes_self(self):
        params = [
            Parameter(name="self"),
            Parameter(name="x", annotation="int"),
        ]
        f = Function(name="method", parameters=params, is_method=True)
        required = f.get_required_params()
        assert len(required) == 1
        assert required[0].name == "x"

    def test_get_optional_params(self):
        params = [
            Parameter(name="x", annotation="int"),
            Parameter(name="y", annotation="int", default="0"),
        ]
        f = Function(name="func", parameters=params)
        optional = f.get_optional_params()
        assert len(optional) == 1
        assert optional[0].name == "y"

    def test_has_var_positional(self):
        params = [Parameter(name="args", kind="var_positional")]
        f = Function(name="func", parameters=params)
        assert f.has_var_positional() is True

    def test_has_var_keyword(self):
        params = [Parameter(name="kwargs", kind="var_keyword")]
        f = Function(name="func", parameters=params)
        assert f.has_var_keyword() is True

    def test_no_varargs(self):
        params = [Parameter(name="x")]
        f = Function(name="func", parameters=params)
        assert f.has_var_positional() is False
        assert f.has_var_keyword() is False

    def test_get_required_excludes_varargs(self):
        params = [
            Parameter(name="x", annotation="int"),
            Parameter(name="args", kind="var_positional"),
            Parameter(name="kwargs", kind="var_keyword"),
        ]
        f = Function(name="func", parameters=params)
        required = f.get_required_params()
        assert len(required) == 1
        assert required[0].name == "x"

    def test_to_dict(self):
        f = Function(name="add", line_number=10, returns="int", decorators=["staticmethod"])
        d = f.to_dict()
        assert d["name"] == "add"
        assert d["line_number"] == 10
        assert d["returns"] == "int"
        assert d["decorators"] == ["staticmethod"]


class TestPythonParser:
    """Tests for the PythonParser class."""

    def test_simple_function(self):
        code = 'def add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n'
        parser = PythonParser(code)
        funcs = parser.parse()
        assert len(funcs) == 1
        f = funcs[0]
        assert f.name == "add"
        assert f.returns == "int"
        assert f.docstring == "Add two numbers."
        assert len(f.parameters) == 2
        assert f.parameters[0].name == "a"
        assert f.parameters[0].annotation == "int"
        assert f.parameters[1].name == "b"
        assert f.is_method is False

    def test_function_with_defaults(self):
        code = "def power(base: float, exponent: int = 2) -> float:\n    return base ** exponent\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        f = funcs[0]
        assert f.parameters[0].default is None
        assert f.parameters[1].default == "2"

    def test_function_no_annotations(self):
        code = "def hello(name):\n    return f'Hello {name}'\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        f = funcs[0]
        assert f.parameters[0].annotation is None
        assert f.returns is None

    def test_class_methods(self):
        code = """
class Calc:
    def __init__(self, val: int = 0):
        self.val = val

    def add(self, amount: int) -> int:
        self.val += amount
        return self.val

    @staticmethod
    def is_valid(s: str) -> bool:
        return True

    @classmethod
    def from_str(cls, s: str) -> "Calc":
        return cls(int(s))
"""
        parser = PythonParser(code)
        funcs = parser.parse()
        assert len(funcs) == 4
        for f in funcs:
            assert f.is_method is True
            assert f.class_name == "Calc"

        # __init__
        assert funcs[0].name == "__init__"
        assert funcs[0].parameters[0].name == "self"

        # add
        assert funcs[1].name == "add"
        assert "staticmethod" in funcs[2].decorators
        assert "classmethod" in funcs[3].decorators

    def test_async_function(self):
        code = "async def fetch(url: str) -> dict:\n    return {}\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        assert len(funcs) == 1
        assert funcs[0].name == "fetch"

    def test_varargs_and_kwargs(self):
        code = "def func(a: int, *args: str, key: bool = True, **kwargs: int):\n    pass\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        f = funcs[0]

        names_and_kinds = [(p.name, p.kind) for p in f.parameters]
        assert ("a", "positional_or_keyword") in names_and_kinds
        assert ("args", "var_positional") in names_and_kinds
        assert ("key", "keyword_only") in names_and_kinds
        assert ("kwargs", "var_keyword") in names_and_kinds

        key_param = [p for p in f.parameters if p.name == "key"][0]
        assert key_param.default == "True"

    def test_keyword_only_args(self):
        code = "def func(a: int, *, b: str, c: int = 5):\n    pass\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        f = funcs[0]

        assert f.parameters[0].name == "a"
        assert f.parameters[0].kind == "positional_or_keyword"
        assert f.parameters[1].name == "b"
        assert f.parameters[1].kind == "keyword_only"
        assert f.parameters[1].default is None
        assert f.parameters[2].name == "c"
        assert f.parameters[2].kind == "keyword_only"
        assert f.parameters[2].default == "5"

    def test_syntax_error(self):
        code = "def broken(:\n    pass\n"
        parser = PythonParser(code)
        with pytest.raises(SyntaxError):
            parser.parse()

    def test_empty_source(self):
        parser = PythonParser("")
        funcs = parser.parse()
        assert funcs == []

    def test_no_functions(self):
        code = "x = 42\ny = 'hello'\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        assert funcs == []

    def test_complex_annotations(self):
        code = "def func(x: List[int], y: Dict[str, Any]) -> Optional[str]:\n    pass\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        f = funcs[0]
        assert "List[int]" in f.parameters[0].annotation
        assert "Dict[str, Any]" in f.parameters[1].annotation
        assert "Optional[str]" in f.returns

    def test_multiple_defaults(self):
        code = "def func(a, b=1, c=2, d=3):\n    pass\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        f = funcs[0]
        assert f.parameters[0].default is None  # a
        assert f.parameters[1].default == "1"   # b
        assert f.parameters[2].default == "2"   # c
        assert f.parameters[3].default == "3"   # d

    def test_decorator_extraction(self):
        code = "@property\ndef val(self):\n    return self._val\n"
        parser = PythonParser(code)
        funcs = parser.parse()
        assert "property" in funcs[0].decorators

    def test_nested_classes(self):
        code = """
class Outer:
    class Inner:
        def method(self):
            pass
"""
        parser = PythonParser(code)
        funcs = parser.parse()
        assert len(funcs) == 1
        assert funcs[0].class_name == "Inner"

    def test_sample_functions_file(self):
        """Parse the included sample file end-to-end."""
        import os
        sample_path = os.path.join(os.path.dirname(__file__), "..", "assets", "sample-functions.py")
        if not os.path.exists(sample_path):
            pytest.skip("sample-functions.py not found")
        with open(sample_path) as f:
            code = f.read()
        parser = PythonParser(code)
        funcs = parser.parse()
        assert len(funcs) > 20
        func_names = [f.name for f in funcs]
        assert "add" in func_names
        assert "divide" in func_names
        assert "create_user" in func_names
