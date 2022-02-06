from functools import partial
from typing import Callable, Optional, Tuple

import numpy as np

# Optional matplotlib imports for graphical representation
try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Ellipse
except ImportError:
    plt = None
    Ellipse = None

# Type definitions
VEC = np.ndarray
COORD = Tuple[float, float]


# Helpers
def bisect(
    f: Callable[[float], float], a: float, b: float, target: float = 0,
    max_iter: int = 1000, precision: float = 10**(-8)
) -> float:
    """Bisection Root-Finding Algorithm

    Parameters:
    -----------
    f : `Callable`[[float], float]
        Function taking one input and producing one output.
    a : float
        Lower search bound.
    b : float
        Upper search bound (b > a).
    target : float, optional
        Target value. Default is `0` (root).
    max_iter : int, optional
        Maximum number of iterations. Default is `100`.
    precision : float, optional
        Acceptable deviation precision. Default is `10E-08`.

    Returns:
    --------
        float
            Approximate function root.
    """
    assert a < b
    assert max_iter > 0

    mid = None
    for _ in range(max_iter):
        mid = (a+b)/2
        val = f(mid) - target

        if abs(val) <= precision:
            return mid
        elif np.sign(f(a)-target) == np.sign(val):
            a = mid
        else:
            b = mid

    return mid


def intersect_circles(
    M0: VEC, r0: float, M1: VEC, r1: float
) -> Optional[Tuple[VEC, Optional[VEC]]]:
    """Find intersection points between two circles

    Algorithm can be derived by focussing on the vector connecting the two
    midpoints. The two intersections lie on the line perpendicular two this
    connecting line. Pythagoras' theorem applies here.

    Parameters:
    -----------
    M0 : `VEC` (numpy.ndarray)
        2D vector to first midpoint.
    r0 : float
        First radius.
    M1 : `VEC` (numpy.ndarray)
        2D vector to second midpoint.
    r1 : float
        Second radius.

    Returns
    -------
    `Optional`[`Tuple`[`VEC`, `Optional`[`VEC`]]]
        Intersections can be 0, 1 (tangent), 2, or infinite (identical circles).

        Infinite or no intersections are returned as `None`. Two intersections
        are returned as a tuple of numpy vectors. The second vector might be
        `None` if only one intersection.
    """
    D = M1 - M0
    d = np.linalg.norm(D)

    # Circles not intersecting and seperate
    if d > (r0 + r1):
        return None
    # Circles contained
    elif d < abs(r0 - r1):
        return None
    # Circles are the same, infinite intersections
    elif d == 0:
        return None

    a = (r0**2 - r1**2 + d**2)/(2*d)
    h = np.sqrt(r0**2 - a**2)

    MID = M0 + D * a/d

    # Circles touching, only one intersection at MID
    if d == (r0 + r1):
        return (MID, None)

    x0 = MID[0] + h*D[1]/d
    y0 = MID[1] - h*D[0]/d

    x1 = MID[0] - h*D[1]/d
    y1 = MID[1] + h*D[0]/d

    return (np.array([x0, y0]), np.array([x1, y1]))


def plt_transfer_ellipse(a: float, focus: VEC, **kwargs) -> Ellipse:
    """Create a transfer ellipse

    Parameters:
    -----------
    a : float
        Semi-major axis of the ellipse (Lambert's problem).
    focus : `VEC` (numpy.ndarray)
        2D vector to vacant focus. The other focus is assumed to lie at the
        origin (0, 0).
    **kwargs
        Keyword arguments passed to `Ellipse` constructor.

    Returns:
    --------
    `matplotlib.patches.Ellipse`
        matplotlib `Ellipse` path to be displayed.
    """
    # Matplotlib required!
    assert Ellipse is not None

    # One of the foci is assumed to be at (0, 0)
    # linear eccentricity
    e = np.linalg.norm(focus)/2
    b = np.sqrt(a**2 - e**2)    # b^2 = a^2 - e^2

    center = focus/2
    angle = np.arctan(focus[1]/focus[0])*(360/(2*np.pi))

    return Ellipse(xy=(center[0], center[1]), width=2*a, height=2*b,
                   angle=angle, **kwargs)


def plot_lambert(R0: VEC, R1: VEC, a: float):
    """Plot solution to Lambert's problem

    Parameters:
    -----------
    R0 : `VEC` (numpy.ndarray)
        Position vector of initial position
    R1 : `VEC` (numpy.ndarray)
        Position vector of final position
    a : float
        Calculated semi-major axis for given transfer time.

    Returns:
    --------
    None
    """
    # Matplotlib required!
    assert plt is not None

    # Get possible empty foci (might be None, 1 or 2)
    intersections = intersect_circles(
        R0, 2*a - np.linalg.norm(R0),
        R1, 2*a - np.linalg.norm(R1)
    )

    fig, ax = plt.subplots()

    ax.plot(R0[0], R0[1], "ro")  # Red marker for R0
    ax.plot(R1[0], R1[1], "ro")  # Red marker for R1
    # Star marker for central body
    ax.plot(0, 0, "y*", markersize=24)

    if intersections is not None:
        I1, I2 = intersections
        ax.add_patch(plt_transfer_ellipse(a, I1, fill=None))
        if I2 is not None:
            ax.add_patch(plt_transfer_ellipse(a, I2, fill=None))

    # Centered x-axis
    ax.spines['bottom'].set_position('zero')
    # Centered y-axis
    ax.spines['left'].set_position('zero')
    # Remove top border
    ax.spines['top'].set_visible(False)
    # Remove right border
    ax.spines['right'].set_visible(False)

    # Equal axes scaling
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()


# Main Code
def calc_alpha(a: float, s: float, long: bool = False) -> float:
    """Calculate alpha angle

    Parameters:
    -----------
    a: float
        Semi-major axis.
    s: float
        Semiperimeter.
    long: bool, optional
        Whether to return alpha for long arc (2pi - alpha). Default is `False`.

    Returns:
    --------
    float
        Alpha angle.
    """
    alpha = 2*np.arcsin(np.sqrt(s/(2*a)))
    if long:
        return 2*np.pi - alpha
    return alpha


def calc_beta(a: float, s: float, c: float, rev: bool = False) -> float:
    """Calculate beta angle

    Parameters:
    -----------
    a: float
        Semi-major axis.
    s: float
        Semiperimeter.
    c: float
        Chord length.
    long: bool, optional
        Whether to return reverse-direction beta (-beta). Default is `False`.

    Returns:
    --------
    float
        Beta angle.
    """
    beta = 2*np.arcsin(np.sqrt((s-c)/(2*a)))
    if rev:
        return -beta
    return beta


def lagrange_eq(
    a: float, mu: float, s: float, c: float, long_arc: bool = False
) -> float:
    """Solve the Lagrange equation for Lambert's problem

    Parameters:
    -----------
    a : float
        Semi-major axis.
    mu : float
        Graviational parameter (mu = G(M+m) approx. GM for M >> m).
    s : float
        Semiperimeter.
    c : float
        Chord
    long_arc: bool, optional
        Whether to take the long arc for the calculation
        (alpha_long = 2*pi - alpha). This can be useful for long flight times.
        Default is `False`.

    Returns:
    --------
    float
        Minimum transfer time for given parameters.
    """
    A = calc_alpha(a=a, s=s, long=long_arc)
    B = calc_beta(a=a, s=s, c=c)
    p = np.sqrt((a**3)/mu)

    return p * ((A - B) - (np.sin(A) - np.sin(B)))


def calc_velocity(
    r0: VEC, r1: VEC, rc: VEC, a: float, alpha: float, beta: float, mu: float
) -> Tuple[float, float]:
    """Calculate skewed velocity vectors

    Parameters:
    -----------
    r0: `VEC` (numpy.ndarray)
        Position vector of initial position.
    r1: `VEC` (numpy.ndarray)
        Position vector of final position.
    rc: `VEC` (numpy.ndarray)
        Chord vector between `r0` and `r1`
    a: float
        Semi-major axis.
    alpha: float
        Alpha angle from Lagrange formula.
    beta: float
        Beta angle from Lagrange formula.
    mu: float
        Gravitational parameter (mu = G(M+m) approx. GM for M >> m).

    Returns:
    --------
    `Tuple`[float, float]
        Vectors of initial and final velocity.
    """
    rc_norm = rc / np.linalg.norm(rc)
    p = np.sqrt(mu/(4*a))

    x = 1/np.tan(beta/2)   # cot(beta/2)
    y = 1/np.tan(alpha/2)  # cot(alpha/2)

    X = x + y  # cot(beta/2) + cot(alpha/2)
    Y = x - y  # cot(beta/2) - cot(alpha/2)

    v1 = p * (X*rc_norm + Y*(r0/np.linalg.norm(r0)))
    v2 = p * (X*rc_norm - Y*(r1/np.linalg.norm(r1)))

    return (v1, v2)


def solve_lambert(
    r0: VEC, r1: VEC, dt: float, mu: float
) -> Tuple[float, float, float]:
    """Solve Lambert's problem

    Parameters:
    -----------
    r0 : `VEC` (numpy.ndarray)
        Position vector of initial position
    r1 : `VEC` (numpy.ndarray)
        Position vector of final position
    dt : float
        Desired transfer time.
    mu : float
        Graviational parameter (mu = G(M+m) approx. GM for M >> m).

    Returns:
    --------
    `Tuple`[float, float, float]
        Tuple of semi-major axis for desired transfer time and corresponding
        initial and final velocity vector.
    """
    R0 = np.linalg.norm(r0)
    R1 = np.linalg.norm(r1)

    c = np.linalg.norm(r1 - r0)
    s = (R0 + R1 + c) / 2

    a_min = s / 2       # a_min = (r1 + r2 + c)/4 = s/2
    a_max = 20 * a_min  # a_max >> a_min

    long_arc = False

    # a_min is longest flight time on short branch
    t_max_short_path = lagrange_eq(a=a_min, mu=mu, s=s, c=c)
    if t_max_short_path < dt:
        print("USING LONG ARC")
        long_arc = True

    lagrange = partial(lagrange_eq, mu=mu, s=s, c=c, long_arc=long_arc)

    a = bisect(lagrange, a=a_min, b=a_max, target=dt)

    alpha = calc_alpha(a=a, s=s, long=long_arc)
    beta = calc_beta(a=a, s=s, c=c)
    v1, v2 = calc_velocity(r0=r0, r1=r1, rc=r1-r0, a=a,
                           alpha=alpha, beta=beta, mu=mu)

    return (a, v1, v2)


if __name__ == "__main__":
    # Example positions at (1, 0) and (1, 0)
    R0 = np.array([1, 0])
    R1 = np.array([0, 1])
    dt = 2
    mu = 4*(np.pi**2)

    a, v1, v2 = solve_lambert(R0, R1, dt, mu)
    print("a = %s, v1 = %s, v2 = %s" % (a, v1, v2))

    if plt is not None:
        plot_lambert(R0, R1, a)
