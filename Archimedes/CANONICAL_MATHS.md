# CANONICAL_MATHS — the Archimedes / PtolemyDesktop equation reference

The single list the Archimedes corpus is built from. One row per equation:
**name**, **expression** (sympy-parseable infix; `^` = power, `*` explicit,
`Integral(f,(x,a,b))` etc.), and **jurisdiction** — the regime a law holds in.
No citations: the equations are public knowledge and the point is that they
**decompose** on the Archimedes side.

Jurisdiction vocabulary:

| tag | meaning |
|---|---|
| `pure` | a mathematical identity — no physical regime |
| `classical` | Newtonian: v≪c, ℏ→0, point/rigid bodies |
| `relativistic` | special relativity, v~c |
| `gr` | general relativity / curved spacetime |
| `quantum` | non-relativistic quantum mechanics |
| `qft` | relativistic quantum field theory (QED/QCD/EW) |
| `continuum` | continuum mechanics & fluids — no molecular detail |
| `statistical` | many-body / thermodynamic limit |
| `linear` | linear / small-signal / small-angle approximation |
| `numerical` | a discretisation or iteration scheme |
| `engineering` | design formula — standardised, safety-factored, or empirical |

Format for downstream tooling: a row is `name | expr | jurisdiction`; the
`###` heading is the **domain**. `Archimedes/Maths/researcher/<tier>/<domain>.py`
is generated from its section.

---

## foundations

### algebra

| name | expr | jurisdiction |
|---|---|---|
| quadratic formula | x = (-b + sqrt(b^2 - 4*a*c))/(2*a) | pure |
| difference of two squares | a^2 - b^2 = (a - b)*(a + b) | pure |
| binomial square | (a + b)^2 = a^2 + 2*a*b + b^2 | pure |
| binomial theorem term | T = binomial(n, k)*a^(n - k)*b^k | pure |
| sum of an arithmetic series | S = n*(a1 + an)/2 | pure |
| sum of a geometric series | S = a*(1 - r^n)/(1 - r) | pure |
| infinite geometric series | S = a/(1 - r) | pure |
| logarithm change of base | log(x, b) = log(x)/log(b) | pure |
| exponential–log inverse | exp(log(x)) = x | pure |
| completing the square | a*x^2 + b*x + c = a*(x + b/(2*a))^2 + c - b^2/(4*a) | pure |
| Vieta sum of roots | r1 + r2 = -b/a | pure |
| Vieta product of roots | r1*r2 = c/a | pure |
| partial fraction (simple pole) | P/((x - p)*(x - q)) = A/(x - p) + B/(x - q) | pure |
| AM–GM inequality (two terms) | (a + b)/2 >= sqrt(a*b) | pure |
| absolute value definition | Abs(x) = sqrt(x^2) | pure |

### linear_algebra

| name | expr | jurisdiction |
|---|---|---|
| 2x2 determinant | det = a*d - b*c | pure |
| matrix inverse (2x2) | Ainv = Matrix([[d, -b], [-c, a]])/(a*d - b*c) | pure |
| eigenvalue equation | A*v = lam*v | pure |
| characteristic polynomial (2x2) | lam^2 - (a + d)*lam + (a*d - b*c) | pure |
| trace equals sum of eigenvalues | tr = lam1 + lam2 | pure |
| determinant equals product of eigenvalues | det = lam1*lam2 | pure |
| dot product | d = ax*bx + ay*by + az*bz | pure |
| vector norm | n = sqrt(vx^2 + vy^2 + vz^2) | pure |
| cross product magnitude | m = Abs(a)*Abs(b)*sin(theta) | pure |
| angle between vectors | cos(theta) = d/(Abs(a)*Abs(b)) | pure |
| projection of a onto b | p = (a_dot_b/b_dot_b)*bmag | pure |
| Cramer's rule (x) | x = det_x/det_A | pure |
| rank–nullity | rank + nullity = n | pure |
| least squares normal equations | AT_A*x = AT_b | numerical |
| Rayleigh quotient | R = xT_A_x/xT_x | pure |

### calculus

| name | expr | jurisdiction |
|---|---|---|
| power rule | d = n*x^(n - 1) | pure |
| product rule | d = u_p*v + u*v_p | pure |
| quotient rule | d = (u_p*v - u*v_p)/v^2 | pure |
| chain rule | d = f_p_of_g*g_p | pure |
| fundamental theorem (evaluation) | I = F_b - F_a | pure |
| integration by parts | I = u*v - Integral(v, u) | pure |
| arc length of a plane curve | L = Integral(sqrt(1 + f_p^2), (x, a, b)) | pure |
| volume of revolution (disc) | V = pi*Integral(f^2, (x, a, b)) | pure |
| Taylor remainder (Lagrange) | R = f_np1_c*(x - a)^(n + 1)/factorial(n + 1) | pure |
| mean value theorem | m = (F_b - F_a)/(b - a) | pure |
| l'Hopital's rule | L = f_p/g_p | pure |
| Newton's method iteration | x1 = x0 - f_x/f_p_x | numerical |
| trapezoidal rule (panel) | I = h/2*(f0 + f1) | numerical |
| Simpson's rule (panel) | I = h/3*(f0 + 4*f1 + f2) | numerical |
| curvature of a plane curve | kappa = Abs(f_pp)/(1 + f_p^2)^(3/2) | pure |

### vector_calculus

| name | expr | jurisdiction |
|---|---|---|
| gradient magnitude | g = sqrt(fx^2 + fy^2 + fz^2) | pure |
| divergence | divF = dFx_dx + dFy_dy + dFz_dz | pure |
| curl z-component | curlz = dFy_dx - dFx_dy | pure |
| Laplacian (scalar) | lap = d2f_dx2 + d2f_dy2 + d2f_dz2 | pure |
| directional derivative | Du = gx*ux + gy*uy + gz*uz | pure |
| divergence theorem | flux = Integral(divF, V) | pure |
| Stokes' theorem | circ = Integral(curlF_n, S) | pure |
| Green's theorem | circ = Integral(dQ_dx - dP_dy, A) | pure |
| line integral of a field | W = Integral(Fx*dx + Fy*dy, C) | pure |
| gradient of a potential | F = -gradV | classical |
| continuity (conservative field) | curlF = 0 | pure |
| Jacobian (2D) | J = xu*yv - xv*yu | pure |

### differential_equations

| name | expr | jurisdiction |
|---|---|---|
| first-order linear ODE (integrating factor) | mu = exp(Integral(P, x)) | pure |
| exponential growth/decay | y = y0*exp(k*t) | classical |
| logistic growth | y = K/(1 + A*exp(-r*t)) | classical |
| simple harmonic oscillator | x = A*cos(omega*t + phi) | classical |
| damped oscillator envelope | x = A*exp(-gamma*t)*cos(omega_d*t) | classical |
| natural frequency (mass–spring) | omega = sqrt(k/m) | classical |
| damped frequency | omega_d = sqrt(omega0^2 - gamma^2) | classical |
| critical damping condition | c = 2*sqrt(k*m) | classical |
| RC circuit decay | V = V0*exp(-t/(R*C)) | linear |
| RL circuit rise | i = (V/R)*(1 - exp(-R*t/L)) | linear |
| heat equation (1D) | df_dt = alpha*d2f_dx2 | continuum |
| wave equation (1D) | d2u_dt2 = c^2*d2u_dx2 | continuum |
| Laplace equation | d2f_dx2 + d2f_dy2 = 0 | continuum |
| Euler method step | y1 = y0 + h*f_of_t0_y0 | numerical |
| RK4 step | y1 = y0 + h/6*(k1 + 2*k2 + 2*k3 + k4) | numerical |

### complex_analysis

| name | expr | jurisdiction |
|---|---|---|
| Euler's formula | exp(I*theta) = cos(theta) + I*sin(theta) | pure |
| modulus | r = sqrt(a^2 + b^2) | pure |
| argument | phi = atan2(b, a) | pure |
| de Moivre's theorem | (cos(theta) + I*sin(theta))^n = cos(n*theta) + I*sin(n*theta) | pure |
| complex conjugate product | z*zbar = a^2 + b^2 | pure |
| Cauchy–Riemann (u_x) | du_dx = dv_dy | pure |
| Cauchy–Riemann (u_y) | du_dy = -dv_dx | pure |
| Cauchy integral formula | f_a = (1/(2*pi*I))*Integral(f/(z - a), C) | pure |
| residue at a simple pole | Res = limit((z - p)*f, z, p) | pure |
| nth roots of unity | w = exp(2*pi*I*k/n) | pure |

### geometry

| name | expr | jurisdiction |
|---|---|---|
| area of a circle | A = pi*r^2 | pure |
| circumference of a circle | C = 2*pi*r | pure |
| area of a triangle | A = b*h/2 | pure |
| Heron's formula | A = sqrt(s*(s - a)*(s - b)*(s - c)) | pure |
| area of a trapezoid | A = (b1 + b2)*h/2 | pure |
| area of an ellipse | A = pi*a*b | pure |
| surface area of a sphere | A = 4*pi*r^2 | pure |
| volume of a sphere | V = 4*pi*r^3/3 | pure |
| volume of a cylinder | V = pi*r^2*h | pure |
| volume of a cone | V = pi*r^2*h/3 | pure |
| Pythagorean theorem | c^2 = a^2 + b^2 | pure |
| distance between two points | d = sqrt((x2 - x1)^2 + (y2 - y1)^2) | pure |
| law of cosines | c^2 = a^2 + b^2 - 2*a*b*cos(C) | pure |
| law of sines | a/sin(A) = b/sin(B) | pure |
| equation of a circle | (x - h)^2 + (y - k)^2 = r^2 | pure |

### trigonometry

| name | expr | jurisdiction |
|---|---|---|
| Pythagorean identity | sin(x)^2 + cos(x)^2 = 1 | pure |
| tangent identity | tan(x) = sin(x)/cos(x) | pure |
| angle sum (sine) | sin(a + b) = sin(a)*cos(b) + cos(a)*sin(b) | pure |
| angle sum (cosine) | cos(a + b) = cos(a)*cos(b) - sin(a)*sin(b) | pure |
| double angle (sine) | sin(2*x) = 2*sin(x)*cos(x) | pure |
| double angle (cosine) | cos(2*x) = 1 - 2*sin(x)^2 | pure |
| half angle (sine) | sin(x/2) = sqrt((1 - cos(x))/2) | pure |
| product to sum | sin(a)*cos(b) = (sin(a + b) + sin(a - b))/2 | pure |
| law of tangents | (a - b)/(a + b) = tan((A - B)/2)/tan((A + B)/2) | pure |
| arc length (radians) | s = r*theta | pure |
| sector area | A = r^2*theta/2 | pure |

### probability

| name | expr | jurisdiction |
|---|---|---|
| conditional probability | P_A_given_B = P_AB/P_B | pure |
| Bayes' theorem | P_A_given_B = P_B_given_A*P_A/P_B | pure |
| complement rule | P_not_A = 1 - P_A | pure |
| addition rule | P_A_or_B = P_A + P_B - P_AB | pure |
| independence | P_AB = P_A*P_B | pure |
| expected value (discrete) | E = Sum(x*p, (i, 1, n)) | pure |
| variance | Var = E_x2 - mu^2 | pure |
| binomial pmf | P = binomial(n, k)*p^k*(1 - p)^(n - k) | pure |
| Poisson pmf | P = exp(-lam)*lam^k/factorial(k) | pure |
| normal pdf | f = exp(-(x - mu)^2/(2*sigma^2))/(sigma*sqrt(2*pi)) | pure |
| exponential pdf | f = lam*exp(-lam*x) | pure |
| standard score | z = (x - mu)/sigma | pure |
| law of large numbers (mean) | xbar = Sum(x, (i, 1, n))/n | statistical |

### statistics

| name | expr | jurisdiction |
|---|---|---|
| sample mean | xbar = Sum(x, (i, 1, n))/n | pure |
| sample variance | s2 = Sum((x - xbar)^2, (i, 1, n))/(n - 1) | pure |
| sample standard deviation | s = sqrt(s2) | pure |
| standard error of the mean | SE = s/sqrt(n) | pure |
| z confidence interval | CI = xbar + zc*SE | pure |
| t statistic | t = (xbar - mu0)/SE | pure |
| Pearson correlation | r = Sxy/sqrt(Sxx*Syy) | pure |
| simple linear regression slope | b1 = Sxy/Sxx | pure |
| simple linear regression intercept | b0 = ybar - b1*xbar | pure |
| coefficient of determination | R2 = 1 - SSres/SStot | pure |
| chi-square statistic | chi2 = Sum((O - E)^2/E, (i, 1, k)) | pure |
| pooled variance | sp2 = ((n1 - 1)*s1^2 + (n2 - 1)*s2^2)/(n1 + n2 - 2) | pure |
| propagation of error (sum) | sf = sqrt(sa^2 + sb^2) | engineering |

### numerical_methods

| name | expr | jurisdiction |
|---|---|---|
| bisection midpoint | c = (a + b)/2 | numerical |
| secant method step | x2 = x1 - f1*(x1 - x0)/(f1 - f0) | numerical |
| fixed-point iteration | x1 = g_of_x0 | numerical |
| finite difference (forward) | fp = (f_xh - f_x)/h | numerical |
| finite difference (central) | fp = (f_xh - f_xmh)/(2*h) | numerical |
| second derivative (central) | fpp = (f_xh - 2*f_x + f_xmh)/h^2 | numerical |
| Lagrange interpolation (2 pt) | y = y0*(x - x1)/(x0 - x1) + y1*(x - x0)/(x1 - x0) | numerical |
| Richardson extrapolation | A = (4*A_h2 - A_h)/3 | numerical |
| condition number | kappa = Abs(x*f_p/f) | numerical |
| relative error | e = Abs(x_approx - x_true)/Abs(x_true) | numerical |
| machine epsilon bound | e <= 2^(-t) | numerical |
| Gauss–Seidel update | xi = (bi - sigma)/aii | numerical |

### discrete

| name | expr | jurisdiction |
|---|---|---|
| permutations | P = factorial(n)/factorial(n - r) | pure |
| combinations | C = factorial(n)/(factorial(r)*factorial(n - r)) | pure |
| Pascal's rule | binomial(n, k) = binomial(n - 1, k - 1) + binomial(n - 1, k) | pure |
| sum of first n integers | S = n*(n + 1)/2 | pure |
| sum of first n squares | S = n*(n + 1)*(2*n + 1)/6 | pure |
| geometric sum (finite) | S = (r^(n + 1) - 1)/(r - 1) | pure |
| inclusion–exclusion (two sets) | Abs(A_or_B) = Abs(A) + Abs(B) - Abs(A_and_B) | pure |
| pigeonhole (min box) | m = ceiling(n/k) | pure |
| Fibonacci recurrence | F = Fm1 + Fm2 | pure |
| Euler's totient (prime power) | phi = p^k - p^(k - 1) | pure |
| handshake lemma | Sum(deg, (i, 1, n)) = 2*E | pure |
| Catalan number | Cn = binomial(2*n, n)/(n + 1) | pure |

### transforms

| name | expr | jurisdiction |
|---|---|---|
| Fourier transform | F = Integral(f*exp(-I*omega*t), (t, -oo, oo)) | pure |
| inverse Fourier transform | f = (1/(2*pi))*Integral(F*exp(I*omega*t), (omega, -oo, oo)) | pure |
| Laplace transform | F = Integral(f*exp(-s*t), (t, 0, oo)) | pure |
| Laplace of a derivative | Lfp = s*F - f0 | linear |
| Parseval's theorem | Integral(Abs(f)^2, t) = (1/(2*pi))*Integral(Abs(F)^2, omega) | pure |
| convolution theorem | L_fg = F*G | linear |
| Z-transform | X = Sum(x*z^(-n), (n, 0, oo)) | pure |
| DFT coefficient | Xk = Sum(x*exp(-2*pi*I*k*n/N), (n, 0, N - 1)) | numerical |
| sampling (Nyquist) | fs = 2*fmax | engineering |
| discrete-time shift | Z_shift = z^(-k)*X | linear |

---

## physics

### classical_mechanics

| name | expr | jurisdiction |
|---|---|---|
| SUVAT velocity | v = u + a*t | classical |
| SUVAT displacement | s = u*t + a*t^2/2 | classical |
| SUVAT time-free | v^2 = u^2 + 2*a*s | classical |
| Newton's second law | F = m*a | classical |
| linear momentum | p = m*v | classical |
| impulse–momentum | J = F*t | classical |
| work by a constant force | W = F*d*cos(theta) | classical |
| kinetic energy | KE = m*v^2/2 | classical |
| gravitational PE (uniform g) | PE = m*g*h | classical |
| average power | P = W/t | classical |
| centripetal force | F = m*v^2/r | classical |
| centripetal acceleration | a = v^2/r | classical |
| angular velocity | omega = v/r | classical |
| Newton's law for rotation | tau = I*alpha | classical |
| angular momentum (rigid body) | L = I*omega | classical |
| rotational kinetic energy | KE = I*omega^2/2 | classical |
| universal gravitation | F = G*M*m/r^2 | classical |
| simple pendulum period | T = 2*pi*sqrt(L/g) | classical |
| mass–spring period | T = 2*pi*sqrt(m/k) | classical |
| Hooke's law | F = -k*x | classical |
| escape velocity | v = sqrt(2*G*M/r) | classical |
| orbital period (Kepler III) | T^2 = 4*pi^2*a^3/(G*M) | classical |

### lagrangian_hamiltonian

| name | expr | jurisdiction |
|---|---|---|
| Lagrangian | L = T - V | classical |
| Euler–Lagrange equation | d_dt_dL_dqdot - dL_dq = 0 | classical |
| generalized momentum | p = dL_dqdot | classical |
| Hamiltonian | H = p*qdot - L | classical |
| Hamilton's equation (q) | qdot = dH_dp | classical |
| Hamilton's equation (p) | pdot = -dH_dq | classical |
| kinetic energy (generalized) | T = M_ij*qdot_i*qdot_j/2 | classical |
| action functional | S = Integral(L, (t, t1, t2)) | classical |
| conserved momentum (cyclic coord) | p = const | classical |
| Poisson bracket | pb = df_dq*dg_dp - df_dp*dg_dq | classical |
| Noether charge | Q = Integral(j0, V) | classical |

### continuum_mechanics

| name | expr | jurisdiction |
|---|---|---|
| Cauchy stress traction | t_i = sigma_ij*n_j | continuum |
| small strain tensor | eps_ij = (du_i_dj + du_j_di)/2 | continuum |
| Hooke's law (isotropic) | sigma_ij = lam*eps_kk*delta_ij + 2*mu*eps_ij | continuum |
| conservation of mass | drho_dt + div_rho_u = 0 | continuum |
| Cauchy momentum equation | rho*Du_Dt = div_sigma + rho*b | continuum |
| material derivative | Df_Dt = df_dt + u_dot_grad_f | continuum |
| volumetric strain | e = eps_xx + eps_yy + eps_zz | continuum |
| bulk modulus relation | K = E/(3*(1 - 2*nu)) | continuum |
| shear modulus relation | G = E/(2*(1 + nu)) | continuum |
| von Mises stress | sv = sqrt(((s1 - s2)^2 + (s2 - s3)^2 + (s3 - s1)^2)/2) | continuum |
| plane strain compatibility | d2exx_dy2 + d2eyy_dx2 = 2*d2exy_dxdy | continuum |

### fluid_dynamics

| name | expr | jurisdiction |
|---|---|---|
| continuity (incompressible) | div_u = 0 | continuum |
| Euler equation | rho*Du_Dt = -grad_p + rho*g | continuum |
| Navier–Stokes (incompressible) | rho*Du_Dt = -grad_p + mu*lap_u + rho*g | continuum |
| Bernoulli equation | p + rho*v^2/2 + rho*g*h = const | continuum |
| hydrostatic pressure | p = p0 + rho*g*h | continuum |
| volumetric flow rate | Q = A*v | continuum |
| Reynolds number | Re = rho*v*Ltag/mu | continuum |
| Mach number | Ma = v/csnd | continuum |
| Froude number | Fr = v/sqrt(g*Ltag) | continuum |
| Darcy–Weisbach head loss | hf = f*(Lp/D)*v^2/(2*g) | engineering |
| Hagen–Poiseuille flow | Q = pi*dP*R^4/(8*mu*Lp) | continuum |
| drag force | Fd = Cd*rho*v^2*A/2 | continuum |
| lift force | Fl = Cl*rho*v^2*A/2 | continuum |
| vorticity (2D) | zeta = dv_dx - du_dy | continuum |
| stream function velocity | u = dpsi_dy | continuum |
| speed of sound (ideal gas) | csnd = sqrt(gamma*Rs*Temp) | continuum |
| dynamic pressure | q = rho*v^2/2 | continuum |

### thermodynamics

| name | expr | jurisdiction |
|---|---|---|
| ideal gas law | P*V = n*Rg*Temp | statistical |
| first law | dU = Qh - Wd | classical |
| work by expansion | Wd = Integral(P, V) | classical |
| enthalpy | Hth = U + P*V | classical |
| entropy change (reversible) | dS = Qh/Temp | statistical |
| Gibbs free energy | Gf = Hth - Temp*S | statistical |
| Helmholtz free energy | Af = U - Temp*S | statistical |
| Carnot efficiency | eta = 1 - Tc/Th | classical |
| heat capacity relation (ideal gas) | Cp - Cv = Rg | statistical |
| adiabatic process (ideal gas) | P*V^gamma = const | classical |
| specific heat | Qh = m*csp*dTemp | classical |
| latent heat | Qh = m*Lh | classical |
| Clausius–Clapeyron | dP_dT = Lh/(Temp*dV) | statistical |
| coefficient of performance (fridge) | COP = Tc/(Th - Tc) | classical |

### heat_transfer

| name | expr | jurisdiction |
|---|---|---|
| Fourier's law of conduction | q = -k*dT_dx | continuum |
| conduction through a slab | Qh = k*A*dTemp/Lth | engineering |
| thermal resistance (slab) | Rth = Lth/(k*A) | engineering |
| Newton's law of cooling | q = h*(Ts - Tinf) | engineering |
| Stefan–Boltzmann radiation | q = eps*sigmaSB*(Ts^4 - Tsur^4) | continuum |
| lumped capacitance cooling | Temp = Tinf + (T0 - Tinf)*exp(-h*A*t/(rho*Vol*csp)) | engineering |
| Biot number | Bi = h*Lc/k | engineering |
| Nusselt number | Nu = h*Lc/kf | engineering |
| Prandtl number | Pr = mu*csp/kf | continuum |
| Rayleigh number | Ra = g*beta*dTemp*Lc^3/(nu*alpha) | continuum |
| log mean temperature difference | LMTD = (dT1 - dT2)/log(dT1/dT2) | engineering |
| fin heat rate (long fin) | Qh = sqrt(h*Pf*k*Ac)*theta_b | engineering |

### statistical_mechanics

| name | expr | jurisdiction |
|---|---|---|
| Boltzmann entropy | S = kB*log(W) | statistical |
| Boltzmann factor | p = exp(-Ei/(kB*Temp))/Zp | statistical |
| partition function | Zp = Sum(exp(-Ei/(kB*Temp)), (i, 1, N)) | statistical |
| average energy from Z | U = -dlogZ_dbeta | statistical |
| equipartition (per quadratic dof) | E = kB*Temp/2 | statistical |
| Maxwell–Boltzmann speed pdf | f = 4*pi*(m/(2*pi*kB*Temp))^(3/2)*v^2*exp(-m*v^2/(2*kB*Temp)) | statistical |
| rms speed | vrms = sqrt(3*kB*Temp/m) | statistical |
| Fermi–Dirac occupation | nf = 1/(exp((E - mu)/(kB*Temp)) + 1) | quantum |
| Bose–Einstein occupation | nb = 1/(exp((E - mu)/(kB*Temp)) - 1) | quantum |
| Planck spectral radiance | B = (2*hb*f^3/csnd^2)/(exp(hb*f/(kB*Temp)) - 1) | quantum |
| pressure from partition function | Pp = kB*Temp*dlogZ_dV | statistical |
| Helmholtz free energy from Z | Af = -kB*Temp*log(Zp) | statistical |

### electromagnetism

| name | expr | jurisdiction |
|---|---|---|
| Coulomb's law | F = ke*q1*q2/r^2 | classical |
| electric field of a point charge | E = ke*q/r^2 | classical |
| electric potential of a point charge | V = ke*q/r | classical |
| Gauss's law | flux_E = Qenc/eps0 | classical |
| Lorentz force | F = q*(Efield + v*Bfield) | classical |
| capacitance (parallel plate) | Cap = eps0*A/dgap | classical |
| energy in a capacitor | Uc = Cap*V^2/2 | classical |
| Ohm's law (microscopic) | J = sigmac*Efield | linear |
| Biot–Savart magnitude | dB = mu0*Ic*dl*sin(theta)/(4*pi*r^2) | classical |
| Ampere's law | circ_B = mu0*Ienc | classical |
| Faraday's law | emf = -dflux_B_dt | classical |
| inductor energy | Ul = Lind*Ic^2/2 | classical |
| Poynting vector magnitude | Sp = Efield*Bfield/mu0 | classical |
| wave speed in vacuum | csnd = 1/sqrt(mu0*eps0) | classical |
| Maxwell–Faraday (curl E) | curl_E = -dB_dt | classical |
| Maxwell–Ampere (curl B) | curl_B = mu0*J + mu0*eps0*dE_dt | classical |

### circuits

| name | expr | jurisdiction |
|---|---|---|
| Ohm's law | V = Ic*R | linear |
| power dissipated | Pw = Ic^2*R | linear |
| resistors in series | Req = R1 + R2 + R3 | linear |
| resistors in parallel | Req = 1/(1/R1 + 1/R2) | linear |
| capacitors in series | Ceq = 1/(1/C1 + 1/C2) | linear |
| capacitors in parallel | Ceq = C1 + C2 | linear |
| capacitive reactance | Xc = 1/(omega*Cap) | linear |
| inductive reactance | Xl = omega*Lind | linear |
| RLC resonant frequency | omega0 = 1/sqrt(Lind*Cap) | linear |
| impedance magnitude (series RLC) | Zmag = sqrt(R^2 + (Xl - Xc)^2) | linear |
| quality factor (series RLC) | Qf = omega0*Lind/R | linear |
| voltage divider | Vout = Vin*R2/(R1 + R2) | linear |
| RC time constant | tau = R*Cap | linear |
| RMS of a sinusoid | Vrms = Vpk/sqrt(2) | linear |
| average AC power | Pw = Vrms*Irms*cos(phi) | linear |

### waves

| name | expr | jurisdiction |
|---|---|---|
| wave speed | vw = fw*lam | classical |
| angular frequency | omega = 2*pi*fw | classical |
| wave number | kw = 2*pi/lam | classical |
| travelling wave | y = A*sin(kw*x - omega*t) | classical |
| speed on a string | vw = sqrt(Ten/mu_lin) | classical |
| standing wave frequencies (string) | fn = nmode*vw/(2*Lstr) | classical |
| Doppler effect (moving source) | fobs = fw*vw/(vw - vs) | classical |
| intensity from power | Iw = Pw/(4*pi*r^2) | classical |
| sound intensity level | dBlvl = 10*log(Iw/I0, 10) | engineering |
| beat frequency | fbeat = Abs(f1 - f2) | classical |
| energy of a wave (SHM element) | Ew = mu_lin*omega^2*A^2/2 | classical |

### optics

| name | expr | jurisdiction |
|---|---|---|
| Snell's law | n1*sin(th1) = n2*sin(th2) | classical |
| critical angle | thc = asin(n2/n1) | classical |
| thin lens equation | 1/fl = 1/dobj + 1/dimg | classical |
| magnification | Mag = -dimg/dobj | classical |
| lensmaker's equation | 1/fl = (nl - 1)*(1/R1 - 1/R2) | classical |
| mirror equation | 1/fl = 1/dobj + 1/dimg | classical |
| double-slit maxima | dslit*sin(theta) = mord*lam | classical |
| single-slit minima | aslit*sin(theta) = mord*lam | classical |
| diffraction grating | dgr*sin(theta) = mord*lam | classical |
| Rayleigh resolution criterion | thmin = 1.22*lam/Dap | classical |
| Bragg's law | 2*dsp*sin(theta) = nord*lam | quantum |
| Malus's law | Iw = I0*cos(theta)^2 | classical |
| Brewster's angle | thb = atan(n2/n1) | classical |

### relativity

| name | expr | jurisdiction |
|---|---|---|
| Lorentz factor | gam = 1/sqrt(1 - v^2/csnd^2) | relativistic |
| time dilation | dt = gam*dtau | relativistic |
| length contraction | Lc = L0/gam | relativistic |
| relativistic momentum | p = gam*m*v | relativistic |
| mass–energy equivalence | E = m*csnd^2 | relativistic |
| total relativistic energy | E = gam*m*csnd^2 | relativistic |
| energy–momentum relation | E^2 = (p*csnd)^2 + (m*csnd^2)^2 | relativistic |
| relativistic velocity addition | w = (u + v)/(1 + u*v/csnd^2) | relativistic |
| relativistic Doppler | fobs = fw*sqrt((1 + beta)/(1 - beta)) | relativistic |
| relativistic kinetic energy | KE = (gam - 1)*m*csnd^2 | relativistic |
| Schwarzschild radius | rs = 2*G*M/csnd^2 | gr |
| gravitational time dilation | dt = dtau/sqrt(1 - rs/r) | gr |
| gravitational redshift | z = 1/sqrt(1 - rs/r) - 1 | gr |
| Einstein field equation (trace form) | Gmn = 8*pi*G*Tmn/csnd^4 | gr |

### quantum_mechanics

| name | expr | jurisdiction |
|---|---|---|
| de Broglie wavelength | lam = hb/p | quantum |
| Planck relation | E = hb*fw | quantum |
| photoelectric effect | KEmax = hb*fw - Wf | quantum |
| time-dependent Schrodinger equation | I*hbar*dpsi_dt = Hop*psi | quantum |
| time-independent Schrodinger equation | Hop*psi = En*psi | quantum |
| Hamiltonian operator (1D) | Hop = -hbar^2*d2_dx2/(2*m) + Vx | quantum |
| Heisenberg uncertainty | dx*dp >= hbar/2 | quantum |
| particle in a box energy | En = nq^2*pi^2*hbar^2/(2*m*Lb^2) | quantum |
| quantum harmonic oscillator energy | En = hbar*omega*(nq + 1/2) | quantum |
| hydrogen energy levels | En = -13.6/nq^2 | quantum |
| expectation value | exp_A = Integral(conjpsi*Aop*psi, x) | quantum |
| probability current (1D) | jprob = hbar*im_conjpsi_dpsidx/m | quantum |
| commutator of x and p | comm_xp = I*hbar | quantum |
| tunnelling transmission (thick barrier) | Tt = exp(-2*sqrt(2*m*(V0 - En))*Lbar/hbar) | quantum |
| Compton shift | dlam = (hb/(m*csnd))*(1 - cos(theta)) | quantum |

### quantum_field_theory

| name | expr | jurisdiction |
|---|---|---|
| Klein–Gordon equation | box_phi + (m*csnd/hbar)^2*phi = 0 | qft |
| Dirac equation | I*hbar*gam_mu*d_mu*psi - m*csnd*psi = 0 | qft |
| free scalar Lagrangian | Ls = d_mu_phi*d_up_phi/2 - m^2*phi^2/2 | qft |
| Maxwell Lagrangian | Lem = -Fmn*Fup_mn/4 | qft |
| QED interaction term | Lint = -qe*psibar*gam_mu*psi*A_mu | qft |
| fine-structure constant | alpha = qe^2/(4*pi*eps0*hbar*csnd) | qft |
| Feynman propagator (scalar) | Gf = I/(pmom^2 - m^2 + I*epsn) | qft |
| Yang–Mills field strength | Fmn = d_mu*Anu - d_nu*Amu + gc*fabc*Ab_mu*Ac_nu | qft |
| running coupling (one loop) | alpha_mu = alpha0/(1 - b0*alpha0*log(mu/mu0)) | qft |
| QCD beta function (one loop) | beta = -b0*gc^3/(16*pi^2) | qft |
| mass–shell condition | pmom^2 = m^2*csnd^2 | qft |
| number current (complex scalar) | jmu = I*(conjphi*d_mu_phi - phi*d_mu_conjphi) | qft |

---

## engineering

### statics

| name | expr | jurisdiction |
|---|---|---|
| sum of forces (x) | Sum(Fx, (i, 1, n)) = 0 | engineering |
| sum of forces (y) | Sum(Fy, (i, 1, n)) = 0 | engineering |
| sum of moments | Sum(Mo, (i, 1, n)) = 0 | engineering |
| moment of a force | Mo = F*d | engineering |
| resultant of two forces | Rf = sqrt(F1^2 + F2^2 + 2*F1*F2*cos(theta)) | engineering |
| centroid (composite, x) | xc = Sum(Ai*xi, (i, 1, n))/Sum(Ai, (i, 1, n)) | engineering |
| friction (impending motion) | Ff = mus*Nf | engineering |
| belt friction | T1 = T2*exp(mus*betawrap) | engineering |
| truss method of joints (joint eq) | Sum(Fx, (i, 1, n)) = 0 | engineering |
| distributed load resultant | Wr = w*Ld | engineering |
| parallel axis theorem | Ix = Ic + Ar*dd^2 | engineering |

### strength_of_materials

| name | expr | jurisdiction |
|---|---|---|
| axial normal stress | sigma = Pf/Ar | continuum |
| axial normal strain | eps = delta/Lb | continuum |
| Hooke's law (uniaxial) | sigma = Em*eps | continuum |
| elongation of an axial bar | delta = Pf*Lb/(Ar*Em) | continuum |
| transverse shear stress in a beam | tau = Vs*Qm/(Im*tw) | continuum |
| flexure formula | sigma = Mb*yb/Im | continuum |
| thermal strain | eps = alpha*dTemp | continuum |
| torsion formula | tau = Tq*rho/Jp | continuum |
| angle of twist | phi = Tq*Lb/(Jp*Gs) | continuum |
| Euler critical buckling load | Pcr = pi^2*Em*Im/(Kf*Lb)^2 | engineering |
| cantilever tip deflection (end load) | dmax = Pf*Lb^3/(3*Em*Im) | engineering |
| simple beam mid-span deflection (UDL) | dmax = 5*wl*Lb^4/(384*Em*Im) | engineering |
| second moment of area (rectangle) | Im = bw*hb^3/12 | continuum |
| shear modulus from E and nu | Gs = Em/(2*(1 + nu)) | continuum |
| factor of safety | FS = sigy/sigma | engineering |
| hoop stress (thin cylinder) | sigma = pi_p*rc/tw | engineering |

### structural

| name | expr | jurisdiction |
|---|---|---|
| beam bending moment (simply supported, centre load) | Mmax = Pf*Lb/4 | engineering |
| beam bending moment (UDL) | Mmax = wl*Lb^2/8 | engineering |
| section modulus | Sm = Im/cdist | engineering |
| required section modulus | Sm = Mmax/sigallow | engineering |
| slenderness ratio | SR = Kf*Lb/rgyr | engineering |
| radius of gyration | rgyr = sqrt(Im/Ar) | engineering |
| axial load capacity (short column) | Pn = sigy*Ar | engineering |
| deflection limit check | dmax <= Lb/360 | engineering |
| combined axial and bending stress | sigma = Pf/Ar + Mb*cdist/Im | engineering |
| shear flow | qsf = Vs*Qm/Im | engineering |
| fixed-fixed buckling factor | Kf = 0.5 | engineering |
| natural frequency of a beam (SS, first mode) | fn = (pi/2)*sqrt(Em*Im/(mu_lin*Lb^4)) | engineering |

### control_theory

| name | expr | jurisdiction |
|---|---|---|
| first-order transfer function | Gs = Kg/(taus*s + 1) | linear |
| second-order transfer function | Gs = wn^2/(s^2 + 2*zeta*wn*s + wn^2) | linear |
| closed-loop transfer function | Tcl = Gs/(1 + Gs*Hs) | linear |
| steady-state error (step, type 0) | ess = 1/(1 + Kp) | linear |
| damping ratio from overshoot | zeta = -log(Mp)/sqrt(pi^2 + log(Mp)^2) | linear |
| settling time (2%) | ts = 4/(zeta*wn) | linear |
| peak time | tp = pi/(wn*sqrt(1 - zeta^2)) | linear |
| percent overshoot | Mp = exp(-pi*zeta/sqrt(1 - zeta^2)) | linear |
| PID controller | u = Kp*e + Ki*Integral(e, t) + Kd*de_dt | linear |
| phase margin condition | PM = 180 + arg_GH | linear |
| gain margin | GM = 1/Abs(GH_at_180) | linear |
| Routh first column (2nd order) | a1*a2 - a0*a3 > 0 | linear |

### signal_processing

| name | expr | jurisdiction |
|---|---|---|
| convolution (discrete) | y = Sum(x*h_shift, (k, 0, N - 1)) | linear |
| moving average filter | y = Sum(x, (k, 0, M - 1))/M | linear |
| discrete Fourier transform | Xk = Sum(x*exp(-2*pi*I*k*n/N), (n, 0, N - 1)) | numerical |
| power spectral density | Sxx = Abs(Xk)^2/N | numerical |
| SNR in decibels | SNRdb = 10*log(Psig/Pnoise, 10) | engineering |
| Nyquist rate | fs = 2*fmax | engineering |
| ideal reconstruction (sinc) | x = Sum(xn*sinc((t - n*Ts)/Ts), (n, -oo, oo)) | linear |
| first-order IIR filter | y = a*x + (1 - a)*yprev | linear |
| group delay | tg = -dphase_domega | linear |
| decibel (amplitude ratio) | dBv = 20*log(V1/V2, 10) | engineering |
| RMS of a discrete signal | xrms = sqrt(Sum(x^2, (n, 0, N - 1))/N) | numerical |
| window main-lobe width (rectangular) | dw = 4*pi/N | numerical |

### materials

| name | expr | jurisdiction |
|---|---|---|
| engineering stress | sigma = Pf/A0 | engineering |
| engineering strain | eps = (Lf - L0)/L0 | engineering |
| true stress | sigt = sigma*(1 + eps) | engineering |
| true strain | epst = log(1 + eps) | engineering |
| Young's modulus (elastic region) | Em = sigma/eps | continuum |
| toughness (area under curve) | Ut = Integral(sigma, eps) | engineering |
| resilience | Ur = sigy^2/(2*Em) | engineering |
| Arrhenius rate | rate = A0*exp(-Ea/(Rg*Temp)) | statistical |
| Hall–Petch relation | sigy = sig0 + kh/sqrt(dgr) | engineering |
| Griffith crack stress | sigf = sqrt(2*Em*gsurf/(pi*ac)) | continuum |
| fracture toughness (mode I) | KIc = Yg*sigf*sqrt(pi*ac) | engineering |
| Paris law (fatigue crack growth) | da_dN = Cp*dK^mp | engineering |
| coefficient of thermal expansion | dL = alpha*L0*dTemp | engineering |
| rule of mixtures (composite modulus) | Ec = Vf*Ef + (1 - Vf)*Emx | engineering |

### chemical_engineering

| name | expr | jurisdiction |
|---|---|---|
| mass balance (steady, no reaction) | min = mout | engineering |
| mole fraction | xa = na/ntot | engineering |
| ideal gas density | rho = P*Mw/(Rg*Temp) | statistical |
| Raoult's law | pa = xa*pa_sat | engineering |
| Antoine equation | log(psat, 10) = Aa - Ba/(Cc + Temp) | engineering |
| Arrhenius rate constant | kc = A0*exp(-Ea/(Rg*Temp)) | statistical |
| first-order reaction | Ca = Ca0*exp(-kc*t) | engineering |
| second-order reaction | 1/Ca = 1/Ca0 + kc*t | engineering |
| CSTR design equation | Vr = Fa0*Xconv/(-ra) | engineering |
| PFR design equation | Vr = Fa0*Integral(1/(-ra), (Xconv, 0, Xf)) | engineering |
| Reynolds number (pipe) | Re = rho*v*Dp/mu | continuum |
| pressure drop (Fanning) | dP = 2*ff*Lp*rho*v^2/Dp | engineering |
| log mean concentration difference | LMCD = (dC1 - dC2)/log(dC1/dC2) | engineering |
| overall heat transfer coefficient | 1/Uo = 1/hi + tw/kw + 1/ho | engineering |

### electrical_power

| name | expr | jurisdiction |
|---|---|---|
| complex power | Sp = Vp*conjIp | linear |
| real power (single phase) | Pw = Vrms*Irms*cos(phi) | linear |
| reactive power | Qr = Vrms*Irms*sin(phi) | linear |
| apparent power | Sa = Vrms*Irms | linear |
| power factor | pf = Pw/Sa | linear |
| three-phase power | Pw = sqrt(3)*Vll*Il*cos(phi) | linear |
| transformer turns ratio | Vp/Vs = Np/Ns | linear |
| transmission line voltage drop | dV = Il*(Rl*cos(phi) + Xl*sin(phi)) | linear |
| line loss | Ploss = 3*Il^2*Rl | linear |
| per-unit impedance | Zpu = Zohm*Sbase/Vbase^2 | engineering |
| synchronous speed | ns = 120*fw/npoles | linear |
| induction motor slip | sl = (ns - nr)/ns | linear |
| capacitor bank for pf correction | Qc = Pw*(tan(phi1) - tan(phi2)) | engineering |

### rf_microwave

| name | expr | jurisdiction |
|---|---|---|
| wavelength from frequency | lam = csnd/fw | classical |
| reflection coefficient | Gam = (Zl - Z0)/(Zl + Z0) | linear |
| VSWR | vswr = (1 + Abs(Gam))/(1 - Abs(Gam)) | linear |
| return loss (dB) | RL = -20*log(Abs(Gam), 10) | engineering |
| input impedance of a line | Zin = Z0*(Zl + I*Z0*tan(betal))/(Z0 + I*Zl*tan(betal)) | linear |
| quarter-wave transformer | Z0 = sqrt(Zin*Zl) | linear |
| Friis transmission | Pr = Pt*Gt*Grx*lam^2/(4*pi*dist)^2 | engineering |
| radar range equation | Pr = Pt*Gt*Grx*lam^2*sigmarcs/((4*pi)^3*dist^4) | engineering |
| skin depth | dskin = sqrt(2/(omega*mu0*sigmac)) | linear |
| free-space path loss (dB) | FSPL = 20*log(4*pi*dist/lam, 10) | engineering |
| resonator quality factor | Qf = omega0*Estored/Ploss | linear |
| noise figure (cascade, stage 1–2) | Ftot = F1 + (F2 - 1)/G1 | engineering |
| thermal noise power | Pn = kB*Temp*BW | statistical |

### fluid_machinery

| name | expr | jurisdiction |
|---|---|---|
| pump head (energy per weight) | Hp = dp/(rho*g) + dv^2/(2*g) + dz | engineering |
| hydraulic power | Ph = rho*g*Q*Hp | engineering |
| pump efficiency | eta = Ph/Pshaft | engineering |
| specific speed | Nsq = Nrpm*sqrt(Q)/Hp^(3/4) | engineering |
| affinity law (flow vs speed) | Q2 = Q1*(N2/N1) | engineering |
| affinity law (head vs speed) | H2 = H1*(N2/N1)^2 | engineering |
| affinity law (power vs speed) | P2 = P1*(N2/N1)^3 | engineering |
| NPSH available | NPSHa = (patm - pv)/(rho*g) - hs - hf | engineering |
| Euler turbomachine equation | wsp = U2*Vt2 - U1*Vt1 | continuum |
| blade tip speed | U = pi*Dimp*Nrpm/60 | engineering |
| torque on an impeller | Tq = rho*Q*(r2*Vt2 - r1*Vt1) | continuum |

### thermodynamic_cycles

| name | expr | jurisdiction |
|---|---|---|
| Carnot efficiency | eta = 1 - Tc/Th | classical |
| Otto cycle efficiency | eta = 1 - 1/CR^(gamma - 1) | classical |
| Diesel cycle efficiency | eta = 1 - (1/CR^(gamma - 1))*((rc^gamma - 1)/(gamma*(rc - 1))) | classical |
| Brayton cycle efficiency | eta = 1 - 1/PR^((gamma - 1)/gamma) | classical |
| Rankine thermal efficiency | eta = (wturb - wpump)/qin | engineering |
| back-work ratio | bwr = wpump/wturb | engineering |
| isentropic turbine work | wturb = h1 - h2s | classical |
| pump work (incompressible) | wpump = vsp*dp | classical |
| heat added (boiler) | qin = h3 - h2 | engineering |
| refrigeration COP | COP = qL/wnet | classical |
| heat pump COP | COP = qH/wnet | classical |
| regenerator effectiveness | eff = (Th_in - Th_out)/(Th_in - Tc_in) | engineering |

---

## Notes for the generator

- Each `###` section → `Archimedes/Maths/researcher/<tier>/<domain>.py` where
  `<tier>` is `foundations` / `physics` / `engineering` per the top-level
  headings. Each row → `build("<expr>", id="<domain>.<slug>", category="<domain>",
  name="<name>")`; the jurisdiction goes in a module-level `JURISDICTION` map
  keyed by id.
- Symbol names avoid sympy builtins (`E`, `I`, `S`, `N`, `O`, `Q`, `beta`,
  `gamma`, `zeta` are used as variables only via `mathengine._parse`'s
  Symbol-forcing; where a clash is likely the name is spelled out —
  `Temp`, `Efield`, `Bfield`, `csnd`, `hbar`, `Rg`, `gam`).
- Archimedes narrates these the same way he narrates the GenerationalLineage
  engine when the Harness is absent — Tour Guide / Professor Librarian mode.
