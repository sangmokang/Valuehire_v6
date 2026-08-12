"""G2 boundary test: the real package must be importable at runtime."""

import humansearch


def test_package_is_importable_at_runtime() -> None:
    assert humansearch.PACKAGE_NAME == "humansearch"
    module_file = humansearch.__file__
    assert module_file is not None
    assert module_file.replace("\\", "/").endswith("src/humansearch/__init__.py")
