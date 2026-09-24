"""
pint.delegates.formatter.typst
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implements:
- Typst: uses vanilla typst.
- Zero: uses typst zero package format.

:copyright: 2022 by Pint Authors, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from ..._typing import Magnitude
from ...compat import Number, Unpack, ndarray
from ._compound_unit_helpers import (
    BabelKwds,
    prepare_compount_unit,
)
from ._format_helpers import (
    FORMATTER,
    formatter,
    join_mu,
    join_unc,
    override_locale,
)
from ._spec_helpers import (
    remove_custom_flags,
    split_format,
)
from .plain import BaseFormatter
from .sorting import SortFunc

if TYPE_CHECKING:
    from ...facets.measurement import Measurement
    from ...facets.plain import PlainQuantity, PlainUnit
    from ...registry import UnitRegistry
    from ...util import ItMatrix


_EXP_PATTERN = re.compile(r"(-?[0-9]\.?[0-9]*)e(-?)\+?0*([0-9]+)")



class TypstFormatter(BaseFormatter):
    """Typst localizable text formatter."""

    def format_magnitude(
        self, magnitude: Magnitude, mspec: str = "", **babel_kwds: Unpack[BabelKwds]
    ) -> str:
        with override_locale(mspec, babel_kwds.get("locale", None)) as format_number:
            mstr = _EXP_PATTERN.sub(r"\1 times 10^(\2\3)", format_number(magnitude))

        return mstr

    def format_unit(
        self,
        unit: PlainUnit | Iterable[tuple[str, Any]],
        uspec: str = "",
        sort_func: SortFunc | None = None,
        **babel_kwds: Unpack[BabelKwds],
    ) -> str:
        numerator, denominator = prepare_compount_unit(
            unit,
            uspec,
            sort_func=sort_func,
            **babel_kwds,
            registry=self._registry,
        )

        numerator = ((f"\"{u}\"", p) for u, p in numerator)
        denominator = ((f"\"{u}\"", p) for u, p in denominator)

        as_ratio = babel_kwds.get("as_ratio", True)
        assert isinstance(as_ratio, bool)

        return formatter(
            numerator,
            denominator,
            as_ratio=as_ratio,
            single_denominator=True,
            product_fmt=" dot ",
            division_fmt=r"{}\/{}",
            power_fmt="{}^({})",
            parentheses_fmt="({})",
        )

    def format_quantity[MagnitudeT: Magnitude](
        self,
        quantity: PlainQuantity[MagnitudeT],
        qspec: str = "",
        sort_func: SortFunc | None = None,
        **babel_kwds: Unpack[BabelKwds],
    ) -> str:
        registry = self._registry

        mspec, uspec = split_format(
            qspec, registry.formatter.default_format, registry.separate_format_defaults
        )

        joint_fstring = "{} {}"

        return join_mu(
            joint_fstring,
            self.format_magnitude(quantity.magnitude, mspec, **babel_kwds),
            self.format_unit(quantity.unit_items(), uspec, sort_func, **babel_kwds),
        )

    def format_uncertainty(
        self,
        uncertainty,
        unc_spec: str = "",
        sort_func: SortFunc | None = None,
        **babel_kwds: Unpack[BabelKwds],
    ) -> str:
        return format(uncertainty, unc_spec).replace("+/-", " plus.minus ")

    def format_measurement(
        self,
        measurement: Measurement,
        meas_spec: str = "",
        sort_func: SortFunc | None = None,
        **babel_kwds: Unpack[BabelKwds],
    ) -> str:
        registry = self._registry

        mspec, uspec = split_format(
            meas_spec,
            registry.formatter.default_format,
            registry.separate_format_defaults,
        )

        unc_spec = remove_custom_flags(meas_spec)

        joint_fstring = r"{} {}"

        return join_unc(
            joint_fstring,
            "(",
            ")",
            self.format_uncertainty(measurement.magnitude, unc_spec, **babel_kwds),
            self.format_unit(measurement.units, uspec, sort_func, **babel_kwds),
        )