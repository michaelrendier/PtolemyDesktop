"""
Tests for the switch registry and combination validator.

Verifies:
  1. All 14 axes are accessible by name.
  2. Each axis's default value is in its declared choices.
  3. SwitchSettings correctly records user-supplied vs default.
  4. Invalid switch values raise InvalidSwitchValueError.
  5. Deferred switch values raise UnsupportedCombinationError with the
     correct target session in the message.
  6. Metadata dict contains all 14 axes.
"""

import pytest

from noether_engine.switches import (
    ALL_AXES, AXIS_BY_NAME,
    SwitchSettings,
    validate_combination,
    UnsupportedCombinationError,
    InvalidSwitchValueError,
    DEFERRED_SWITCH_VALUES,
    summarize_implementation_status,
)


def test_all_fourteen_axes_exist():
    assert len(ALL_AXES) == 14
    # Names unique
    names = [ax.name for ax in ALL_AXES]
    assert len(set(names)) == 14


def test_each_default_is_valid_choice():
    for ax in ALL_AXES:
        assert ax.default in ax.choices, (
            f"Axis {ax.name}: default '{ax.default}' not in choices {ax.choices}"
        )


def test_settings_records_user_supplied():
    s = SwitchSettings.from_kwargs(theorem='first', signature='mostly_plus')
    assert s.get('theorem') == 'first'
    assert s.get('signature') == 'mostly_plus'
    # User-supplied
    assert not s.is_default('theorem')
    assert not s.is_default('signature')
    # Default
    assert s.is_default('shell')
    assert s.is_default('invariance')


def test_invalid_switch_value_raises():
    with pytest.raises(InvalidSwitchValueError):
        SwitchSettings.from_kwargs(theorem='nonexistent')


def test_invalid_switch_name_raises():
    with pytest.raises(InvalidSwitchValueError):
        SwitchSettings.from_kwargs(not_a_switch='something')


def test_deferred_combination_raises_with_session_number():
    # spacetime=curved is deferred to session 3
    s = SwitchSettings.from_kwargs(spacetime='curved')
    with pytest.raises(UnsupportedCombinationError) as excinfo:
        validate_combination(s)
    msg = str(excinfo.value)
    assert 'spacetime' in msg
    assert 'curved' in msg
    assert 'session 3' in msg


def test_implemented_combination_passes():
    s = SwitchSettings.from_kwargs()  # all defaults
    validate_combination(s)  # should not raise


def test_metadata_dict_has_all_axes():
    s = SwitchSettings.from_kwargs(theorem='first')
    meta = s.as_metadata_dict()
    for ax in ALL_AXES:
        assert ax.name in meta
        entry = meta[ax.name]
        assert 'value' in entry
        assert 'user_supplied' in entry
        assert 'choices' in entry
        assert 'references' in entry


def test_deferred_entries_have_session_number():
    for (name, val), status in DEFERRED_SWITCH_VALUES.items():
        assert status.status == 'deferred'
        assert status.session is not None
        assert isinstance(status.session, int)
        assert status.session >= 2


def test_summarize_produces_nonempty_string():
    s = summarize_implementation_status()
    assert len(s) > 100
    assert 'IMPLEMENTED' in s
    assert 'DEFERRED' in s
