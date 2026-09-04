"""Classical mechanics — kinematics, dynamics, energy, momentum, rotation."""
from __future__ import annotations

from ...mathengine import build

CATEGORY = "classical_mechanics"
PAGE = {
    "title": "Classical Mechanics",
    "blurb": "Point-particle and rigid-body motion: SUVAT, Newton's laws, "
             "work-energy, momentum, circular and rotational motion, gravitation.",
    "source": "Halliday, Resnick & Walker; Kleppner & Kolenkow; NIST",
}

_C = CATEGORY

DEFS = [
    build("v = u + a*t", id="mech.suvat_v", category=_C,
          name="SUVAT: velocity from acceleration",
          units={"v": "m/s", "u": "m/s", "a": "m/s**2", "t": "s"}, source="SUVAT"),
    build("s = u*t + a*t**2/2", id="mech.suvat_s", category=_C,
          name="SUVAT: displacement",
          units={"s": "m", "u": "m/s", "a": "m/s**2", "t": "s"}, source="SUVAT"),
    build("v**2 = u**2 + 2*a*s", id="mech.suvat_vsq", category=_C,
          name="SUVAT: time-free",
          units={"v": "m/s", "u": "m/s", "a": "m/s**2", "s": "m"}, source="SUVAT"),
    build("F = m*a", id="mech.newton_second", category=_C,
          name="Newton's second law",
          units={"F": "N", "m": "kg", "a": "m/s**2"}, source="Newton; NIST"),
    build("p = m*v", id="mech.momentum", category=_C, name="linear momentum",
          units={"p": "kg*m/s", "m": "kg", "v": "m/s"}, source="Newton"),
    build("J = F*t", id="mech.impulse", category=_C, name="impulse",
          units={"J": "N*s", "F": "N", "t": "s"}, source="impulse-momentum"),
    build("W = F*d*cos(theta)", id="mech.work", category=_C,
          name="work done by a constant force",
          units={"W": "J", "F": "N", "d": "m"}, source="work-energy"),
    build("KE = m*v**2/2", id="mech.kinetic_energy", category=_C,
          name="kinetic energy",
          units={"KE": "J", "m": "kg", "v": "m/s"}, source="work-energy"),
    build("PE = m*g*h", id="mech.grav_pe", category=_C,
          name="gravitational potential energy (uniform g)",
          units={"PE": "J", "m": "kg", "g": "m/s**2", "h": "m"}, source="Newton"),
    build("P = W/t", id="mech.power", category=_C, name="average power",
          units={"P": "W", "W": "J", "t": "s"}, source="definition"),
    build("F = m*v**2/r", id="mech.centripetal", category=_C,
          name="centripetal force",
          units={"F": "N", "m": "kg", "v": "m/s", "r": "m"}, source="circular motion"),
    build("a = v**2/r", id="mech.centripetal_accel", category=_C,
          name="centripetal acceleration",
          units={"a": "m/s**2", "v": "m/s", "r": "m"}, source="circular motion"),
    build("omega = v/r", id="mech.angular_velocity", category=_C,
          name="angular velocity from tangential speed",
          units={"omega": "rad/s", "v": "m/s", "r": "m"}, source="rotation"),
    build("tau = I*alpha", id="mech.newton_rotational", category=_C,
          name="Newton's second law for rotation",
          units={"tau": "N*m", "I": "kg*m**2", "alpha": "rad/s**2"}, source="rotation"),
    build("L = I*omega", id="mech.angular_momentum", category=_C,
          name="angular momentum of a rigid body",
          units={"L": "kg*m**2/s", "I": "kg*m**2", "omega": "rad/s"}, source="rotation"),
    build("KE = I*omega**2/2", id="mech.rotational_ke", category=_C,
          name="rotational kinetic energy",
          units={"KE": "J", "I": "kg*m**2", "omega": "rad/s"}, source="rotation"),
    build("F = G*M*m/r**2", id="mech.newton_gravitation", category=_C,
          name="Newton's law of universal gravitation",
          units={"F": "N", "M": "kg", "m": "kg", "r": "m"}, source="Newton; CODATA G"),
    build("T = 2*pi*sqrt(L/g)", id="mech.pendulum_period", category=_C,
          name="period of a simple pendulum (small angle)",
          units={"T": "s", "L": "m", "g": "m/s**2"}, source="SHM"),
    build("T = 2*pi*sqrt(m/k)", id="mech.spring_period", category=_C,
          name="period of a mass on a spring",
          units={"T": "s", "m": "kg", "k": "N/m"}, source="SHM"),
    build("F = -k*x", id="mech.hookes_law", category=_C, name="Hooke's law",
          units={"F": "N", "k": "N/m", "x": "m"}, source="Hooke"),
]
