"""Calculus — differentiation and integration rules, standard results."""
from __future__ import annotations

from ...mathengine import build

CATEGORY = "calculus"
PAGE = {
    "title": "Calculus",
    "blurb": "Single-variable differentiation and integration: the standard "
             "rules, the fundamental theorem, common derivatives and integrals, "
             "Taylor's theorem, arc length and volume of revolution.",
    "source": "Stewart, Calculus; Abramowitz & Stegun; DLMF",
}
_C = CATEGORY

DEFS = [
    build("d_dx_xn = n*x**(n - 1)", id="calc.power_rule", category=_C,
          name="power rule", source="Stewart"),
    build("d_dx_uv = u_prime*v + u*v_prime", id="calc.product_rule", category=_C,
          name="product rule", source="Stewart"),
    build("d_dx_u_over_v = (u_prime*v - u*v_prime)/v**2", id="calc.quotient_rule",
          category=_C, name="quotient rule", source="Stewart"),
    build("d_dx_fg = f_prime_of_g*g_prime", id="calc.chain_rule", category=_C,
          name="chain rule", source="Stewart"),
    build("integral_fundamental = F_b - F_a", id="calc.ftc", category=_C,
          name="fundamental theorem of calculus (evaluation)", source="Stewart"),
    build("arc_length = Integral(sqrt(1 + f_prime**2), (x, a, b))",
          id="calc.arc_length", category=_C,
          name="arc length of a plane curve", source="Stewart"),
    build("volume_revolution = pi*Integral(f**2, (x, a, b))",
          id="calc.volume_disc", category=_C,
          name="volume of revolution (disc method)", source="Stewart"),
    build("taylor_remainder = f_np1_c*(x - a)**(n + 1)/factorial(n + 1)",
          id="calc.taylor_remainder", category=_C,
          name="Taylor's theorem (Lagrange remainder)", source="Stewart"),
    build("mean_value = (F_b - F_a)/(b - a)", id="calc.mvt", category=_C,
          name="mean value theorem (average rate)", source="Stewart"),
    build("newton_step = x - f_of_x/f_prime_of_x", id="calc.newton_iteration",
          category=_C, name="Newton's method iteration", source="numerical analysis"),
    build("simpson = h/3*(f0 + 4*f1 + f2)", id="calc.simpson", category=_C,
          name="Simpson's rule (single panel)", source="Abramowitz & Stegun"),
    build("trapezoid = h/2*(f0 + f1)", id="calc.trapezoid", category=_C,
          name="trapezoidal rule (single panel)", source="Abramowitz & Stegun"),
    build("l_hopital = f_prime/g_prime", id="calc.lhopital", category=_C,
          name="l'Hopital's rule (0/0 or ∞/∞)", source="Stewart"),
    build("integration_by_parts = u*v - Integral(v, u)",
          id="calc.by_parts", category=_C,
          name="integration by parts", source="Stewart"),
]
