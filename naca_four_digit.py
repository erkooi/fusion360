################################################################################
# Copyright 2023 E. Kooistra
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
# Author: Eric Kooistra
# Date: 9 Oct 2023
"""Calculate NACA 4 digit airfoil profile from formulas in [1]:

- M first digit, m = T/100 defines the maximum amount of camber
- P second digit, p = P / 10 is the location of maximum camber from the
    front edge as a fraction of the chord length
- T last two digits, t = T / 100 is the maximum thickness as a fraction of the
    chord length

Usage:

python naca_four_digit.py -M 1 -P 4 -T 8 -x 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --plot

References:
[1] Formulas from:
    https://en.wikipedia.org/wiki/NACA_airfoil
[2] NACA_1408 look up table from:
    http://airfoiltools.com/airfoil/details?airfoil=naca1408-il
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

################################################################################
# Constants

np.set_printoptions(precision=6)

# Lookup tables generated with NACA 4 digit generator [2]
# Chord x-coordinates
# NACA_X = np.flip(np.array(
#          [1.00, 0.95, 0.90, 0.80, 0.70,
#           0.60, 0.50, 0.40, 0.30, 0.25,
#           0.20, 0.15, 0.10, 0.075, 0.05,
#           0.025, 0.0125, 0.0]))
#
# # NACA_1408 look up table
# NACA_1408_UP_X = np.flip(np.array(
#                  [1.00000, 0.95016, 0.90027, 0.80039, 0.70041,
#                   0.60034, 0.50020, 0.40000, 0.29950, 0.24926,
#                   0.19904, 0.14889, 0.09883, 0.07386, 0.04896,
#                   0.02418, 0.01189, 0.00000]))
# NACA_1408_UP_Y = np.flip(np.array(
#                  [0.00084, 0.00698, 0.01271, 0.02305, 0.03193,
#                   0.03931, 0.04502, 0.04869, 0.04939, 0.04819,
#                   0.04574, 0.04171, 0.03558, 0.03138, 0.02602,
#                   0.01862, 0.01324, 0.00000]))
# NACA_1408_LO_X = np.array(
#                  [0.00000, 0.01311, 0.02582, 0.05104, 0.07614,
#                   0.10117, 0.15111, 0.20096, 0.25074, 0.30050,
#                   0.40000, 0.49980, 0.59966, 0.69959, 0.79961,
#                   0.89973, 0.94984, 1.00000])
# NACA_1408_LO_Y = np.array(
#                  [0.00000, -0.01200, -0.01620, -0.02134, -0.02458,
#                   -0.02682, -0.02953, -0.03074, -0.03101, -0.03063,
#                   -0.02869, -0.02556, -0.02153, -0.01693, -0.01193,
#                   -0.00659, -0.00378, -0.00084])
#

# 20 (Up) + 1 (front edge) + 20 (Lo) = 41 points on chord x axis
NACA_X = np.arange(0, 1.01, 0.05)

# NACA 1408 Airfoil M=1.0% P=40.0% T=8.0%
NACA_1408_UP_X = np.flip(np.array(
                 [1.000028, 0.950164, 0.900268, 0.850342, 0.800389,
                  0.750410, 0.700407, 0.650383, 0.600338, 0.550275,
                  0.500196, 0.450103, 0.400000, 0.349752, 0.299500,
                  0.249257, 0.199044, 0.148887, 0.098830, 0.048964,
                  0.000000]))
NACA_1408_UP_Y = np.flip(np.array(
                 [0.000840, 0.006972, 0.012703, 0.018054, 0.023039,
                  0.027662, 0.031923, 0.035811, 0.039309, 0.042390,
                  0.045015, 0.047135, 0.048687, 0.049500, 0.049383,
                  0.048195, 0.045738, 0.041711, 0.035572, 0.026019,
                  0.000000]))
NACA_1408_LO_X = np.array(
                 [0.000000, 0.051036, 0.101170, 0.151113, 0.200956,
                  0.250743, 0.300500, 0.350248, 0.400000, 0.449897,
                  0.499804, 0.549725, 0.599662, 0.649617, 0.699593,
                  0.749590, 0.799611, 0.849658, 0.899732, 0.949836,
                  0.999972])
NACA_1408_LO_Y = np.array(
                 [0.000000, -0.021332, -0.026822, -0.029523, -0.030738,
                  -0.031008, -0.030633, -0.029813, -0.028687, -0.027274,
                  -0.025571, -0.023640, -0.021532, -0.019283, -0.016923,
                  -0.014468, -0.011928, -0.009304, -0.006592, -0.003777,
                  -0.000840])

# NACA 6309 Airfoil M=6.0% P=30.0% T=9.0%
NACA_6309_UP_X = np.flip(np.array(
                 [1.000160, 0.950951, 0.901578, 0.852055, 0.802391,
                  0.752596, 0.702679, 0.652647, 0.602508, 0.552270,
                  0.501942, 0.451537, 0.401066, 0.350546, 0.300000,
                  0.247036, 0.194313, 0.142138, 0.090951, 0.041569,
                  0.000000]))
NACA_6309_UP_Y = np.flip(np.array(
                 [0.000931, 0.014239, 0.026661, 0.038216, 0.048915,
                  0.058764, 0.067757, 0.075880, 0.083113, 0.089421,
                  0.094760, 0.099072, 0.102285, 0.104305, 0.105013,
                  0.102794, 0.095987, 0.084310, 0.067268, 0.043625,
                  0.000000]))
NACA_6309_LO_X = np.array(
                 [0.000000, 0.058431, 0.109049, 0.157862, 0.205687,
                  0.252964, 0.300000, 0.349454, 0.398934, 0.448463,
                  0.498058, 0.547730, 0.597492, 0.647353, 0.697321,
                  0.747404, 0.797609, 0.847945, 0.898422, 0.949049,
                  0.999840])
NACA_6309_LO_Y = np.array(
                 [0.000000, -0.006959, -0.000602, 0.005690, 0.010679,
                  0.013873, 0.014987, 0.015083, 0.015266, 0.015418,
                  0.015444, 0.015273, 0.014846, 0.014120, 0.013060,
                  0.011644, 0.009860, 0.007703, 0.005176, 0.002291,
                  -0.000931])

# Maximum delta margin
NACA_DELTA_X = 0.0000001
NACA_DELTA_Y = 0.000001


################################################################################
# Functions
def digits_to_coefficients(M, P, T):
    """Translate NACA 4 digits into airfoil coefficients."""
    return (M / 100, P / 10, T / 100)


def profile_name_string(M, P, T):
    """String of NACA 4 digit profile name."""
    return 'NACA_' + '%d' % M + '%d' % P + '%02d' % T


def is_naca_1408(M, P, T):
    """Check whether the NACA digits represent NACA_1408 profile.

    Input:
    . M, P, T the four integer digits in NACA_MPxx
    Return:
    . True when profile is NACA_1408, False when not.
    """
    return True if M == 1 and P == 4 and T == 8 else False


def is_naca_00xx(M, P):
    """Check whether the NACA digits represent a symmetrical profile.

    Input:
    . M, P, T the four integer digits in NACA_MPxx
    Return:
    . True when profile is symmetrical, False when cambered.
    """
    return True if M == 0 or P == 0 else False


def combine_array_coordinates(x, xe):
    """Combine array x with array xe in accending order and without duplicates
    """
    xc = np.concatenate((x, xe))  # combine
    xc = np.unique(xc)  # remove duplicates
    xc = np.sort(xc)  # accending order
    return xc


def remove_array_coordinates(x, xe, keepEnds=True):
    """Remove coordinates in array x that are closest to coordinates in array xe

    If keepEnds is True, then do not remove first or last index if that it the
    closest.
    """
    # Find indices of x closest to xe
    indexList = []
    lastIdx = len(x) - 1
    for ei in xe:
        idx = np.argmin(np.abs(x - ei))
        if idx not in indexList:
            if keepEnds:
                if idx != 0 and idx != lastIdx:
                    indexList.append(idx)
            else:
                indexList.append(idx)
    # Remove indices from x
    return np.delete(x, indexList)


def floats_to_string(floats, width=8, decimals=5):
    """Put array of floats into a string
    """
    floatsStr = ''
    for fi, flt in enumerate(floats):
        if fi == 0:
            floatsStr += '%*.*f' % (width, decimals, flt)
        else:
            floatsStr += ', %*.*f' % (width, decimals, flt)
    return floatsStr


def parse_float_string(csf):
    """Parse string of comma separated floats into np.array.

    Input:
    . csf: string of comma separated floats
    Return:
    . floats[]: float values from csf
    """
    floats = csf.split(',')
    floats = [float(x) for x in floats if x]
    return np.array(floats)


def parse_range_string(csf):
    """Parse string of comma separated range of floats into np.array.

    Input:
    . csf: string of comma separated floats to define start, stop, step for
      arange with optional extra values
    Return:
    . floats[]: float values from csf in accending order
    """
    values = csf.split(',')
    if len(values) >= 3:
        # range values
        start = float(values[0])
        stop = float(values[1])
        step = float(values[2])
        floats = np.arange(start, stop, step)
        # extra values
        if len(values) > 3:
            values = values[3:]
            extra = [float(x) for x in values if x]
            floats = combine_array_coordinates(floats, extra)
    else:
        # default values
        floats = np.arange(0, 1.01, 0.05)
    return np.array(floats)


def calculate_symmetrical_profile(T, x, closed=False):
    """Symmetrical NACA_00xx profile, with T = 'xx' for the maximum thickness.

    From [1]:
    If a zero-thickness trailing edge is required, one of the coefficients
    should be modified such that the terms sum to zero. Modifying the last
    coefficient (i.e. to -0.1036, because then a0 + a1 + a2 + a3 + a4 = 0) will
    result in the smallest change to the overall shape of the airfoil.

    Input:
    . T last two digits, for maximum thickness
    . x[]: profile x coordinates along the chord, in range 0 to 1.0
    . closed: when True adjust a4 to close rear edge [2]
    Return:
    . ys[]: the half thickness of the symmetrical profile as function of x
    """
    _, _, t = digits_to_coefficients(0, 0, T)
    a0 = 0.2969
    a1 = -0.1260
    a2 = -0.3516
    a3 = 0.2843
    a4 = -0.1015
    if closed:
        a4 = -0.1036
    ys = 5 * t * (a0 * x**0.5 +
                  a1 * x +
                  a2 * x**2 +
                  a3 * x**3 +
                  a4 * x**4)
    return ys


def calculate_camber_offset(M, P, x):
    """ Calculate mean camber line offset yc for NACA_MPxx profile.

    Input:
    . M first digit, for maximum camber
    . P second digit, for location of maximum camber.
    . x[]: profile x coordinates along the chord, in range 0 to 1.0
    Return:
    . yc[]: mean camber line offsets as function of x
    """
    N = len(x)
    if is_naca_00xx(M, P):
        return np.zeros(N)  # Symmetrical, no camber offset

    # Camber offset
    m, p, _ = digits_to_coefficients(M, P, 0)
    k = len(x[(x <= p)])
    yc = np.zeros(N)
    yc[0:k] = (m / p**2) * (2 * p * x[0:k] - x[0:k]**2)
    yc[k:N] = (m / (1 - p)**2) * ((1 - 2 * p) + 2 * p * x[k:N] - x[k:N]**2)
    return yc


def calculate_camber_angle(M, P, x):
    """ Calculate mean camber line angle theta for NACA_MPxx profile.

    Input:
    . M first digit, for the maximum camber
    . P second digit, is the location of maximum camber.
    . x[]: profile x coordinates along the chord, in range 0 to 1.0
    Return:
    . theta[]: mean camber line angles as function of x
    """
    N = len(x)
    if is_naca_00xx(M, P):
        return np.zeros(N)  # Symmetrical, no camber

    # Camber angle
    m, p, _ = digits_to_coefficients(M, P, 0)
    k = len(x[(x <= p)])
    d_yc_dx = np.zeros(N)
    d_yc_dx[0:k] = (2 * m / p**2) * (p - x[0:k])
    d_yc_dx[k:N] = (2 * m / (1 - p)**2) * (p - x[k:N])
    theta = np.arctan(d_yc_dx)
    return theta


def calculate_cambered_profile(M, P, T, xi, profile, closed=False):
    """Cambered NACA_MPxx profile, with T = 'xx' for the maximum thickness.

    The xi coordinates get modified due to the camber angle != 0. The xi
    modification differs for upper and lower profile, due to that the camber
    offset is perpendicular to profile.

    Input:
    . M, P, T the four integer digits in NACA_MPxx
    . xi[]: input x coordinates for profile, range 0 to 1.0
    . profile: use x for 'upper' or 'lower' profile
    . closed: when True close rear edge [2]
    Return:
    . xp[], yp[]: x, y coordinates for cambered profile
    """
    ySymmetrical = calculate_symmetrical_profile(T, xi, closed)
    offset = calculate_camber_offset(M, P, xi)
    theta = calculate_camber_angle(M, P, xi)
    if profile == 'upper':
        xp = xi - ySymmetrical * np.sin(theta)
        yp = offset + ySymmetrical * np.cos(theta)
    else:
        xp = xi + ySymmetrical * np.sin(theta)
        yp = offset - ySymmetrical * np.cos(theta)
    return (xp, yp)


def report_delta_check(dMax, dMargin, coordinateName):
    """Report error message for coordinateName when dMac >= dMargin.

    Return: True when ok, False when there is a too large mismatch.
    """
    if dMax >= dMargin:
        print('ERROR: Too large delta for %s: ' % coordinateName +
              str(dMax) + ' >= ' + str(dMargin))
        return False
    return True


def verify_naca_x_y(M, P, T):
    """Self test to verify that calculated NACA profile coordinates agree with
    lookup table values, to within a small margin NACA_DELTA_X for x and a
    small margin NACA_DELTA_Y for y coordinates.

    The x coordinates are found arbitrary accurate using iteration. The
    corresponding y coordinates should then match the NACA_EXPECTED_UP_Y and
    NACA_EXPECTED_LO_Y values from the look up table.

    Return: True when ok, False when there is a too large mismatch.
    """
    debug = False
    result = False
    mptStr = '%d%d%02d' % (M, P, T)
    if mptStr == '1408':
        NACA_EXPECTED_UP_X = NACA_1408_UP_X
        NACA_EXPECTED_LO_X = NACA_1408_LO_X
        NACA_EXPECTED_UP_Y = NACA_1408_UP_Y
        NACA_EXPECTED_LO_Y = NACA_1408_LO_Y
    elif mptStr == '6309':
        NACA_EXPECTED_UP_X = NACA_6309_UP_X
        NACA_EXPECTED_LO_X = NACA_6309_LO_X
        NACA_EXPECTED_UP_Y = NACA_6309_UP_Y
        NACA_EXPECTED_LO_Y = NACA_6309_LO_Y
    else:
        print('ERROR: Can not verify NACA-%s' % mptStr)
        return False

    # Iterate to get xi for xp within accuracy NACA_1408_DELTA_X
    repeat = 10  # maximum number of iterations
    rep = 0
    xiUp = NACA_X
    xiLo = NACA_X
    if debug:
        print('')
        print('verify_naca_%s_x_y:' % mptStr)
    while rep <= repeat:
        # Calculate xp, yp for xi
        xpUp, ypUp = calculate_cambered_profile(M, P, T, xiUp, 'upper')
        xpLo, ypLo = calculate_cambered_profile(M, P, T, xiLo, 'lower')
        # . Determine differences with expected profile x, y coordinates
        # . The difference dxUp = -dxLo, see calculate_cambered_profile().
        #   For xi = p the difference 0, because xi = p marks the (flat) top of
        #   the camber, so there the slope d_yc_dx = 0.
        # . Also calculate yp accuracy for print.
        dxUp = xpUp - NACA_EXPECTED_UP_X
        dxLo = xpLo - NACA_EXPECTED_LO_X
        dyUp = ypUp - NACA_EXPECTED_UP_Y
        dyLo = ypLo - NACA_EXPECTED_LO_Y
        dxUpMax = np.max(np.abs(dxUp))
        dxLoMax = np.max(np.abs(dxLo))
        dyUpMax = np.max(np.abs(dyUp))
        dyLoMax = np.max(np.abs(dyLo))
        if debug:
            print('rep = ', rep)
            print('')
            print('xiUp           = ', floats_to_string(xiUp))
            print('xiLo           = ', floats_to_string(xiLo))
            print('NACA_%s_UP_X = ' % mptStr, floats_to_string(NACA_EXPECTED_UP_X))
            print('xpUp           = ', floats_to_string(xpUp))
            print('NACA_%s_LO_X = ' % mptStr, floats_to_string(NACA_EXPECTED_LO_X))
            print('xpLo           = ', floats_to_string(xpLo))
            print('')
            print('NACA_%s_UP_Y = ' % mptStr, floats_to_string(NACA_EXPECTED_UP_Y))
            print('ypUp           = ', floats_to_string(ypUp))
            print('NACA_%s_LO_Y = ' % mptStr, floats_to_string(NACA_EXPECTED_LO_Y))
            print('ypLo           = ', floats_to_string(ypLo))
            print('')
            print('dxUp           = ', floats_to_string(dxUp))
            print('dxLo           = ', floats_to_string(dxLo))
            print('dyUp           = ', floats_to_string(dyUp))
            print('dyLo           = ', floats_to_string(dyLo))
            print('')
            print('dxUpMax = ', dxUpMax)
            print('dxLoMax = ', dxLoMax)
            print('dyUpMax = ', dyUpMax)
            print('dyLoMax = ', dyLoMax)
            print('')
        # . Check required accuracy of x coordinate
        if dxUpMax < NACA_DELTA_X and dxLoMax < NACA_DELTA_X:
            print('Verification of NACA-%s went PASSED.' % mptStr)
            result = True
            break
        # . Prepare next iteration
        # . Offset xi by the negative difference, so that xpUp and xpLo will
        #   become the requested xp value. The slope d_yc_dx of the camber is a
        #   linear function of x, see calculate_camber_angle(), so if xi
        #   results in xp + dx, then xi - dx will result in xp, with sufficient
        #   accuracy.
        xiUp = xiUp - dxUp
        xiLo = xiLo - dxLo
        rep += 1
    # Verify xp value
    result = report_delta_check(dxUpMax, NACA_DELTA_X, 'naca_%s X upper coordinate' % mptStr) and result
    result = report_delta_check(dxLoMax, NACA_DELTA_X, 'naca_%s X lower coordinate' % mptStr) and result
    # Verify yp value
    result = report_delta_check(dyUpMax, NACA_DELTA_Y, 'naca_%s Y upper coordinate' % mptStr) and result
    result = report_delta_check(dyLoMax, NACA_DELTA_Y, 'naca_%s Y lower coordinate' % mptStr) and result
    return result


if __name__ == '__main__':
    import sys

    debug = False

    ############################################################################
    # Verify results, only continue when OK
    if not verify_naca_x_y(1, 4, 8):
        sys.exit()
    if not verify_naca_x_y(6, 3, 9):
        sys.exit()

    ############################################################################
    # Parse arguments
    _parser = argparse.ArgumentParser('naca_four_digit')
    _parser.add_argument('-M', default=1, type=int, help='first digit, maximum camber')
    _parser.add_argument('-P', default=4, type=int, help='second digit, location of maximum camber')
    _parser.add_argument('-T', default=8, type=int,
                         help='last two digits, maximum thickness as a fraction of the chord')
    _parser.add_argument('-x', default='', type=str, help='x coordinates for profile')
    _parser.add_argument('-xUp', default='', type=str, help='x coordinates for upper profile')
    _parser.add_argument('-xLo', default='', type=str, help='x coordinates for lower profile')
    _parser.add_argument('--plot', default=False, action='store_true',
                         help='when True then plot profiles.')
    args = _parser.parse_args()

    M = args.M
    P = args.P
    T = args.T
    profileName = profile_name_string(M, P, T)

    # Constant True when profile is symmetical, else False when cambered
    NACA_00XX = is_naca_00xx(M, P)

    # Constant True when profile is NACA_1408, else False
    NACA_1408 = is_naca_1408(M, P, T)

    # Get X coordinates
    # . default
    if NACA_00XX:
        # . symmetrical
        xaUp = NACA_X
        xaLo = NACA_X
    else:
        xaUp = NACA_1408_UP_X
        xaLo = NACA_1408_LO_X
    # . user specific
    if args.x:
        xaUp = parse_range_string(args.x)
        xaLo = parse_range_string(args.x)
    else:
        if args.xUp:
            xaUp = parse_range_string(args.xUp)
        if args.xLo:
            xaLo = parse_range_string(args.xLo)

    ############################################################################
    # Calculate profile
    xUp, yUp = calculate_cambered_profile(M, P, T, xaUp, 'upper')
    xLo, yLo = calculate_cambered_profile(M, P, T, xaLo, 'lower')

    ############################################################################
    # Print results
    print('args.x:')
    print(profileName + ' args.xUp:' + str(xaUp))
    print(profileName + ' args.xLo:' + str(xaLo))
    print('x:')
    print(profileName + ' xUp:' + str(xUp))
    print(profileName + ' xLo:' + str(xLo))
    print('y:')
    print(profileName + ' yUp:' + str(yUp))
    print(profileName + ' yLo:' + str(yLo))
    print('')

    ############################################################################
    # Calculate camber for plotting
    xc = np.arange(0, 1.01, 0.05)
    offset = calculate_camber_offset(M, P, xc)
    theta = calculate_camber_angle(M, P, xc)

    ############################################################################
    # Plot results
    if args.plot:
        # Plot profile
        figNr = 1
        plt.figure(figNr)
        if NACA_00XX:
            plt.title(profileName + ': Symmetrical profile')
            plt.plot(xUp, yUp, 'b', xUp, yUp, 'bo',
                     xLo, yLo, 'b', xLo, yLo, 'bo')
        elif NACA_1408:
            plt.title(profileName + ': Profile with camber')
            plt.plot(NACA_1408_UP_X, NACA_1408_UP_Y, 'r',
                     NACA_1408_LO_X, NACA_1408_LO_Y, 'r',
                     xUp, yUp, 'b', xUp, yUp, 'bo',
                     xLo, yLo, 'b', xLo, yLo, 'bo',
                     xc, offset, 'g')
            plt.legend(('naca_1408', '',
                        'calculated', '', '', '',
                        'camber', ''), loc='best')
        else:
            plt.title(profileName + ': Profile with camber')
            plt.plot(xUp, yUp, 'b', xUp, yUp, 'bo',
                     xLo, yLo, 'b', xLo, yLo, 'bo',
                     xc, offset, 'g')
            plt.legend(('calculated', '', '', '',
                        'camber', ''), loc='best')
        plt.xlabel('x in mm')
        plt.ylabel('z in mm')
        plt.axis('equal')
        plt.grid()

        # Plot camber
        if not NACA_00XX:
            figNr += 1
            plt.figure(figNr)
            plt.title(profileName + ': Camber angle')
            plt.plot(xc, np.rad2deg(theta), 'r')
            plt.xlabel('x in mm')
            plt.ylabel('theta in degrees')
            plt.grid()
        plt.show()
