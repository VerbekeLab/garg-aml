import logging

import garg_aml


def test_version_is_a_string():
    assert isinstance(garg_aml.__version__, str)
    assert garg_aml.__version__


def test_library_attaches_no_handlers_of_its_own():
    # A library configures no logging; the application decides.
    handlers = logging.getLogger("garg_aml").handlers
    assert all(isinstance(h, logging.NullHandler) for h in handlers)


def test_public_api_is_explicit():
    assert isinstance(garg_aml.__all__, list)
