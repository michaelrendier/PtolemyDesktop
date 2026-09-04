"""Strength of materials — stress, strain, beams, columns, torsion."""
from __future__ import annotations

from ...mathengine import build

CATEGORY = "strength_of_materials"
PAGE = {
    "title": "Strength of Materials",
    "blurb": "Axial stress and strain, Hooke's law, thermal strain, beam "
             "bending and deflection, shafts in torsion, Euler column buckling, "
             "combined loading and factor of safety.",
    "source": "Hibbeler, Mechanics of Materials; Roark's Formulas for Stress "
              "and Strain; Shigley",
}
_C = CATEGORY

DEFS = [
    build("sigma = P/A", id="som.axial_stress", category=_C,
          name="axial normal stress",
          units={"sigma": "Pa", "P": "N", "A": "m**2"}, source="Hibbeler"),
    build("epsilon = delta/L", id="som.axial_strain", category=_C,
          name="axial normal strain",
          units={"delta": "m", "L": "m"}, source="Hibbeler"),
    build("sigma = E*epsilon", id="som.hookes_law_1d", category=_C,
          name="Hooke's law (uniaxial)",
          units={"sigma": "Pa", "E": "Pa"}, source="Hooke; Hibbeler"),
    build("delta = P*L/(A*E)", id="som.axial_deformation", category=_C,
          name="elongation of an axially loaded bar",
          units={"delta": "m", "P": "N", "L": "m", "A": "m**2", "E": "Pa"},
          source="Hibbeler"),
    build("tau = V*Q/(I*t)", id="som.shear_stress_beam", category=_C,
          name="transverse shear stress in a beam",
          units={"tau": "Pa", "V": "N", "I": "m**4", "t": "m"}, source="Hibbeler"),
    build("sigma = M*y/I", id="som.flexure_formula", category=_C,
          name="flexure formula (bending stress)",
          units={"sigma": "Pa", "M": "N*m", "y": "m", "I": "m**4"}, source="Hibbeler"),
    build("epsilon_th = alpha*dT", id="som.thermal_strain", category=_C,
          name="thermal strain", units={"dT": "K"}, source="Hibbeler"),
    build("tau = T*rho/J", id="som.torsion_formula", category=_C,
          name="torsion formula (shear stress in a circular shaft)",
          units={"tau": "Pa", "T": "N*m", "rho": "m", "J": "m**4"}, source="Hibbeler"),
    build("phi = T*L/(J*G)", id="som.angle_of_twist", category=_C,
          name="angle of twist of a circular shaft",
          units={"phi": "rad", "T": "N*m", "L": "m", "J": "m**4", "G": "Pa"},
          source="Hibbeler"),
    build("P_cr = pi**2*E*I/(K*L)**2", id="som.euler_buckling", category=_C,
          name="Euler critical buckling load",
          units={"P_cr": "N", "E": "Pa", "I": "m**4", "L": "m"}, source="Euler; Shigley"),
    build("delta_max = P*L**3/(3*E*I)", id="som.cantilever_tip_deflection",
          category=_C, name="cantilever tip deflection under an end load",
          units={"delta_max": "m", "P": "N", "L": "m", "E": "Pa", "I": "m**4"},
          source="Roark"),
    build("delta_max = 5*w*L**4/(384*E*I)", id="som.simple_beam_udl_deflection",
          category=_C, name="simply supported beam mid-span deflection under UDL",
          units={"delta_max": "m", "w": "N/m", "L": "m", "E": "Pa", "I": "m**4"},
          source="Roark"),
    build("I = b*h**3/12", id="som.second_moment_rectangle", category=_C,
          name="second moment of area of a rectangle",
          units={"I": "m**4", "b": "m", "h": "m"}, source="Hibbeler"),
    build("G = E/(2*(1 + nu))", id="som.shear_modulus", category=_C,
          name="shear modulus from Young's modulus and Poisson's ratio",
          units={"G": "Pa", "E": "Pa"}, source="isotropic elasticity"),
    build("FS = sigma_y/sigma", id="som.factor_of_safety", category=_C,
          name="factor of safety",
          units={"sigma_y": "Pa", "sigma": "Pa"}, source="Shigley"),
]
