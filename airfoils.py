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
# Date: 5 Mar 2023
"""Airfoil

Right-handed coordinates X, Y, Z:
. right hand fingers point from X to Y points tumb to Z
. screw from X to Y goes to Z

    z
    |          . angleYZ
    |--- y     . angleZX
   /           . angleXY
  x

Wing profiles in zx-plane:
  . x = 0 is front edge
  . x = 1 is rear edge
  . y < 0 is left wing
  . z > 0 is top of wing
  Assume that the fuselage has nose at the origin (x, y, z) = (0, 0, 0) and
  tail at positive x and top in positive z direction. Then the wing profile is
  in the zx-plane, with left wing tip at negative y and rigth wing tip at
  positive y. Two wing profiles, one near the fuselage and one at the wing tip,
  are sufficient to create the wing body using a loft in Fusion360.

References:

[1] formulas: https://en.wikipedia.org/wiki/NACA_airfoil, or
[2] lookup tables: http://airfoiltools.com/search/index

The coordinates for the NACA 4-digit profiles are defined by formulas [1] or
lookup tables [2]. These are available via naca_four_digit.py.

Run airfoils.py to scale and redefine the airfoil coordinates (in mm) in the
zx-plane.

- chord_len = chord length of profile scales the profile
- scale_z = scale factor for profile thickness, applied on profile before
    applying rear_width_z.
- rear_width_z = defines z-thickness of the wing rear edge. Applied by adding a
    linearly (when exponent_width = 1) increasing z-offset from 0 at rear edge
    to rear_width_z at rear edge. Separate for top and bottom profile, so
    rear edge width = 2 * rear_width_z. Purpose of rear_width_z > 0 is to avoid
    knive sharp rear edge, so to control how the rear edge will be 3D-printed.
    The NACA-1408 profile has 0.00084 width, which is 0.4 mm for chord_len =
    477.
- exponent_width = applies a exponent_width power value <= 1 to increase the
    z-offset along the chord, front zero at the front edge to rear_width_z at
    the rear edge. When exponent_width = 1 then the z_offset increases linearly.
    When exponent_width < 1 then more z-offset is applied at the front edge.
    For exponent_width << 1 it is as if the z_offset is 0 at the front edge
    and then almost fully applied for the remainder of the chord.
    Use exponent_width > 1 to have smallest change to the overall shape of the
    airfoil. Use exponent_width = 4 to effectively adapt the x**4 coefficient
    in the airfoil formula [1]. Thereforedefault use exponent_width = 4.
- wing_twist = defines rear edge z-offset in mm, that is used to determine the
    twistAngle. Using same rear edge offset along the wing causes that the
    wing profile gets rotated by the twistAngle around the front edge as
    center. The rotation twistAngle increases towards the wing tip, because
    the wing chord length decreases towards the wing tip, so twistAngle =
    arctan(wing_twist / chord_len) increases. The front edge of the wing is
    used as rotation center, so the front edge coordinate does not change.
    Purpose of positive wing_twist is to ensure that the wing tip is the last
    part of the wing surface to stall, see
    https://en.wikipedia.org/wiki/Wing_twist
- tangent_angle = tangent angle for front point of spline, default=-90.0 for
    round front edge. If 0 then use default angle created by spline.
- tangent_length = tangent length for front point of spline, default=0.0 to use
    default length created by spline
- xn = normalized x coordinates in range 0 to 1.0
- xa = extra absolute x coordinates that get normalized and combined with xn
- xfit = when True then iterate to calculate exact matching X coordinates in
    csv output file, else the x coordinates will slightly differ from the
    requested xn + xa due to the camber.
- tx = x-offset,
- ty = y-offset,
- tz = z-offset, (tx, ty, tz) offset coordinate for front edge center of
    profile. To place the wing profile at build location relative to the
    fuselage.
- decimals = 2, for 0.01 mm accuracy in rounded airfoil profile coordinates.

Usage:
# on command line
D:
cd "git\\<script dir>"
# or:
cd /d/git/<script dir>
# to recreate NACA-1408 profiles for f35b model:
# . the wing rear edge is 2 * rear_width_z = 2 * 0.8 = 1.6 mm thick
# . the wing_twist is zero at the fuselage and increases linearly towards the
#   wing tip where it is arctan(wing_twist / chord_len) = arctan(4 / 152) =
#   1.51 degrees.

# Default wing profiles for fuselage, bin corners and wing tip at y = 175, 213,
# 250, 526
python airfoils.py --chord_len 477 --tx 746 --ty -175 --tz 19 --xfit --rear_width 0.8 --rear_arc 0.6 --wing_twist 0 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 772,783,797,820,895,983,1100,1142,1204
python airfoils.py --chord_len 441 --tx 772 --ty -213 --tz 19 --xfit --rear_width 0.8 --rear_arc 0.6 --wing_twist 0 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 783,797,820,895,983,1100,1142,1204
python airfoils.py --chord_len 407 --tx 797 --ty -250 --tz 19 --xfit --rear_width 0.8 --rear_arc 0.6 --wing_twist 0 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 820,895,983,1100,1142
python airfoils.py --chord_len 152 --tx 983 --ty -526 --tz 19 --xfit --rear_width 0.8 --rear_arc 0.6 --wing_twist 4 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 1100

# Extra wing profiles for bin at y = 200, 225 --> Not used, because ybin loft
# is smoother without these intermediate profile
python airfoils.py --chord_len 453.3 --tx 763.1 --ty -200 --tz 19 --xfit ^
                   --rear_width 0.8 --rear_arc 0.6 --wing_twist 0 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 772,783,797,820,895,983,1100,1142,1204
python airfoils.py --chord_len 430.0 --tx 780.1 --ty -225 --tz 19 --xfit ^
                   --rear_width 0.8 --rear_arc 0.6 --wing_twist 0 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 783,797,820,895,983,1100,1142,1204

# Thicker profiles to model bin bottom at y = 175, 213. Use NACA-1408 for top
# and part of NACA-1416 with wider rear_width for bottom.
# . Inreasing rear_width by 1 mm makes the bin bottom at the middle about 0.5
#   mm lower, because exponent_width 1 applies rear_width linearly along the
#   chord.
# . Adapt some points z coordinate near end of chord to connect to z = 19 - 0.8
#   = 18.2 at end of chord.
# . For y = -175 choose T, exponent_width, rear_width to yield smooth bottom
#   bin shape, that is similar to F35B bottom bin shape
python airfoils.py -M 1 -P 4 -T 16 --exponent_width 1 --rear_width 20 ^
                   --chord_len 477 --tx 746 --ty -175 --tz 19 --xfit --wing_twist 0 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 772,783,797,820,895,983,1100,1142,1204
# . For y = -213 choose same T, choose chord_len = 431 somewhere smaller than
#   441 and longer than 1213 - 797 = 416 then choose rear_width 431 / 477 * 20
#   ~= 18. Adapt tx = 782 to make sure rear coordinates match, so 782 + 431 =
#   772 + 441 = 1213 of default wing profile.
python airfoils.py -M 1 -P 4 -T 16 --exponent_width 1 --rear_width 18 ^
                   --chord_len 431 --tx 782 --ty -213 --tz 19 --xfit --wing_twist 0 ^
                   --xn 0,1.1,0.1,0.95,0.25,0.15,0.075,0.05,0.025,0.0125 --xa 797,820,895,983,1100,1142,1204

# GOE-444 ~= NACA-0006
python airfoils.py --profile GOE-444 --chord_len 477 --rear_width 0.8 --exponent_width 0.5

# in iPython:
import os
filepath='D:\\git\\<script dir>'
os.chdir(filepath)
run airfols.py
"""

import numpy as np
import naca_four_digit


################################################################################
# Constants
unit = 'mm'  # input in mm and output csv in mm


################################################################################
# Functions
def Rxz(angle):
    """Rotation matrix to rotate by angle radians from x to z."""
    co, si = np.cos(angle), np.sin(angle)
    return np.array([[co, -si],
                     [si, co]])


def determine_rear_width_offset_curve(zArr, zRearWidth, xNormArr, xNormExponent):
    """Determine offset curve from 0 at front edge to zRearWidth at rear edge.

    Input:
    . zArr: z coordinate values of the profile
    . zRearWidth: requested width for z value of chord rear end
    . xNormArr: normalized x coordinates of the profile
    . xNormExponent: power of x that is used as weight to determine transition
          curve for going from 0 width at front edge to will zRearWidth at
          rear edge.
    Return:
    . zOffsetsArr: offset curve values
    """
    rearWidth = zArr[-1]
    offsetWidth = zRearWidth - rearWidth
    zOffsetsArr = offsetWidth * np.power(xNormArr, xNormExponent)
    # print(rearWidth)
    return zOffsetsArr


def apply_wing_twist(xArr, zArr, angle):
    """Rotate x, y coordinate pairs from xArr, yArr by angle radians."""
    xx = np.zeros(xArr.size)
    zz = np.zeros(zArr.size)
    i = 0
    for x, z in zip(xArr, zArr):
        v = Rxz(angle) @ np.array([x, z])
        xx[i] = v[0]
        zz[i] = v[1]
        i += 1
    return xx, zz


def calculate_twist_angle(args):
    """Calculate wing twist angle from args."""
    return np.arctan2(args.wing_twist_z, args.chord_len)


def calculate_thickness():
    """Calculate wing thickness from args."""
    return args.chord_len * args.T / 100


def calculate_wing_profile(profile_top_x,
                           profile_top_z,
                           profile_bottom_x,
                           profile_bottom_z,
                           chord_len,
                           scale_z,
                           rear_width_z, exponent_width,
                           twistAngle,
                           tx, tz):
    """Calculate wing profile from normalized airfoil profile in XZ plane.

    Input:
    . profile_*: normalized airfoil x, z coordinates for top and bottom
    . *: see script arguments
    Return:
    . wingProfilesTuple: wing profile x, z coordinates for top and bottom
    . wingOffsetsTuple: offsets curve for rear_width_z for top and bottom
    """
    # Start with normalize airfoil profile
    wing_top_x = np.copy(profile_top_x)
    wing_top_z = np.copy(profile_top_z)
    wing_bottom_x = np.copy(profile_bottom_x)
    wing_bottom_z = np.copy(profile_bottom_z)

    # Apply chord_len, scale_z
    wing_top_x *= chord_len
    wing_top_z *= chord_len * scale_z
    wing_bottom_x *= chord_len
    wing_bottom_z *= chord_len * scale_z

    # Apply rear_width_z offset along x chord line
    wing_top_offsets_z = determine_rear_width_offset_curve(
                         wing_top_z, rear_width_z, profile_top_x, exponent_width)
    wing_bottom_offsets_z = determine_rear_width_offset_curve(
                            wing_bottom_z, -1 * rear_width_z, profile_bottom_x, exponent_width)

    wing_top_z += wing_top_offsets_z
    wing_bottom_z += wing_bottom_offsets_z

    # Apply wing_twist_z
    wing_top_x, wing_top_z = apply_wing_twist(wing_top_x, wing_top_z, twistAngle)
    wing_bottom_x, wing_bottom_z = apply_wing_twist(wing_bottom_x, wing_bottom_z, twistAngle)

    # Keep wing edge vertical and at chord_len, this is a small adjustment of ~0.1
    # mm, because twistAngle is only few degrees.
    wing_top_x[-1] = chord_len
    wing_bottom_x[-1] = chord_len

    # Apply tx, tz
    wing_top_x += tx
    wing_top_z += tz
    wing_bottom_x += tx
    wing_bottom_z += tz

    # Return tuples
    wingProfilesTuple = (wing_top_x, wing_top_z, wing_bottom_x, wing_bottom_z)
    wingOffsetsTuple = (wing_top_offsets_z, wing_bottom_offsets_z)
    return (wingProfilesTuple, wingOffsetsTuple)


def calculate_wing_naca(args):
    """Calculate NACA four digit wing profile in XZ plane.

    - Use formula to calculate normalized profile
    - Iterate to exact x coordinates if args.xfit, else use x coordinates that
      are slightly modified due to camber.

    Input:
    . args: user options

    Return:
    . wingProfilesTuple: wing profile x, z coordinates for top and bottom
    . wingOffsetsTuple: offsets curve for rear_width_z for top and bottom
    . wingParametersTuple: derived parameters
    """
    M = args.M
    P = args.P
    T = args.T
    profileBaseName = naca_four_digit.profile_name_string(M, P, T)
    # Derived parameters
    thickness = args.chord_len * T / 100
    twistAngle = calculate_twist_angle(args)
    # Get normalized x coordinates for airfoil profile
    xnUp = xn
    xnLo = xn
    # Calculate normalized profile
    xiUp = xnUp
    xiLo = xnLo
    xUp, yUp = naca_four_digit.calculate_cambered_profile(M, P, T, xiUp, 'upper')
    xLo, yLo = naca_four_digit.calculate_cambered_profile(M, P, T, xiLo, 'lower')
    # Calculate wing profile
    wingProfilesTuple, wingOffsetsTuple = calculate_wing_profile(xUp,
                                                                 yUp,
                                                                 xLo,
                                                                 yLo,
                                                                 args.chord_len,
                                                                 args.scale_z,
                                                                 args.rear_width_z, args.exponent_width,
                                                                 twistAngle,
                                                                 args.tx, args.tz)
    # Iterate to get exact x coordinates
    if args.xfit:
        debug = False
        result = False
        DELTA_X = 0.0000001  # Maximum delta margin
        repeat = 10  # maximum number of iterations
        rep = 0
        while rep <= repeat:
            # . Determine normalized x coordinates
            wing_top_x, _, wing_bottom_x, _ = wingProfilesTuple
            xUp = (wing_top_x - args.tx) / args.chord_len
            xLo = (wing_bottom_x - args.tx) / args.chord_len
            # . Determine difference
            dxUp = xUp - xnUp
            dxLo = xLo - xnLo
            # . Check required accuracy
            dxUpMax = np.max(np.abs(dxUp))
            dxLoMax = np.max(np.abs(dxLo))
            if debug:
                print('rep     = ', rep)
                print('xnUp    = ', naca_four_digit.floats_to_string(xnUp))
                print('xUp     = ', naca_four_digit.floats_to_string(xUp))
                print('dxUp    = ', naca_four_digit.floats_to_string(dxUp))
                print('dxUpMax = ', dxUpMax)
                print('')
                print('xnLo    = ', naca_four_digit.floats_to_string(xnLo))
                print('xLo     = ', naca_four_digit.floats_to_string(xLo))
                print('dxLo    = ', naca_four_digit.floats_to_string(dxLo))
                print('dxLoMax = ', dxLoMax)
                print('')
            if dxUpMax < DELTA_X and dxLoMax < DELTA_X:
                result = True
                break
            # . Prepare next iteration
            # . Offset xi by the negative difference, so that xUp and xLo
            #   will become the requested xn value
            xiUp = xiUp - dxUp
            xiLo = xiLo - dxLo
            # Calculate normalized profile
            xUp, yUp = naca_four_digit.calculate_cambered_profile(M, P, T, xiUp, 'upper')
            xLo, yLo = naca_four_digit.calculate_cambered_profile(M, P, T, xiLo, 'lower')
            # Calculate wing profile
            wingProfilesTuple, wingOffsetsTuple = calculate_wing_profile(xUp,
                                                                         yUp,
                                                                         xLo,
                                                                         yLo,
                                                                         args.chord_len,
                                                                         args.scale_z,
                                                                         args.rear_width_z, args.exponent_width,
                                                                         twistAngle,
                                                                         args.tx, args.tz)
            rep += 1
        if result:
            print('Fitted x coordinates after %d iterations' % rep)
        else:
            print('ERROR: args.xfit failed (%d iterations)' % rep)
    wingParametersTuple = (profileBaseName, thickness)
    return (wingProfilesTuple, wingOffsetsTuple, wingParametersTuple)


def calculate_wing_goe444(args):
    """Calculate GOE-444 wing profile in XZ plane.

    - Use lookup table values with normalized profile.

    Input:
    . args: user options

    Return:
    . wingProfilesTuple: wing profile x, z coordinates for top and bottom
    . wingOffsetsTuple: offsets curve for rear_width_z for top and bottom
    . wingParametersTuple: derived parameters
    """
    profileBaseName = 'GOE-444'
    # Lookup normalized profile
    goe_444_x = np.array(
                [0.0000000, 0.0125000, 0.0250000, 0.0500000, 0.0750000,
                 0.1000000, 0.1500000, 0.2000000, 0.3000000, 0.4000000,
                 0.5000000, 0.6000000, 0.7000000, 0.8000000, 0.9000000,
                 0.9500000, 1.0000000])

    goe_444_z_top = np.array(
                    [0.0000000, 0.0060000, 0.0090000, 0.0130000, 0.0160000,
                     0.0190000, 0.0230000, 0.0255000, 0.0280000, 0.0280000,
                     0.0270000, 0.0240000, 0.0195000, 0.0140000, 0.0080000,
                     0.0045000, 0.0000000])
    goe_444_z_bottom = -1 * goe_444_z_top
    # Derived parameters
    thickness = args.chord_len * np.max(goe_444_z_top) * 2
    twistAngle = calculate_twist_angle(args)
    # Calculate wing profile
    wingProfilesTuple, wingOffsetsTuple = calculate_wing_profile(goe_444_x,
                                                                 goe_444_z_top,
                                                                 goe_444_x,
                                                                 goe_444_z_bottom,
                                                                 args.chord_len,
                                                                 args.scale_z,
                                                                 args.rear_width_z, args.exponent_width,
                                                                 twistAngle,
                                                                 args.tx, args.tz)
    wingParametersTuple = (profileBaseName, thickness)
    return (wingProfilesTuple, wingOffsetsTuple, wingParametersTuple)


def save_csv_wing_profile(args, filepathname, wingProfilesTuple, wingParametersTuple):
    """Save wing profile coordinates in CSV sketch file.

    - Write parameters from args and wingParametersTuple in CSV comment
    - Sketch wing profile in offset XZ plane
      . Round values to args.decimals
      . Use spline for wing profile
      . Use arc or line to close rear of wing if it is not closed
    """
    # Extract tuples
    wing_top_x, wing_top_z, wing_bottom_x, wing_bottom_z = wingProfilesTuple
    unit, profileBaseName, profileNormal, thickness, tangentAngle, twistAngle = wingParametersTuple

    # Round values
    wing_top_x = np.round(wing_top_x, decimals=args.decimals)
    wing_top_z = np.round(wing_top_z, decimals=args.decimals)
    wing_bottom_x = np.round(wing_bottom_x, decimals=args.decimals)
    wing_bottom_z = np.round(wing_bottom_z, decimals=args.decimals)
    ty = np.round(args.ty, decimals=args.decimals)

    # Create wing profile spline
    N_top = wing_top_x.size
    N_bottom = wing_bottom_x.size
    N = N_top + N_bottom
    wing_spline = np.zeros((N, 2))
    i = 0
    for x, z in zip(np.flip(wing_top_x), np.flip(wing_top_z)):
        wing_spline[i][0] = x
        wing_spline[i][1] = z
        i += 1
    for x, z in zip(wing_bottom_x, wing_bottom_z):
        wing_spline[i][0] = x
        wing_spline[i][1] = z
        i += 1

    # Account for twistAngle in front tangent angle
    tangentAngle += np.rad2deg(twistAngle)

    with open(filepathname, 'w') as fp:
        # Write comment
        fp.write('# Wing profile sketch created with airfoils.py:\n')
        fp.write('# . profileBaseName: %s\n' % profileBaseName)
        fp.write('# --chord_len      : %.*f\n' % (args.decimals, args.chord_len))
        fp.write('# . thickness      : %.*f\n' % (args.decimals, thickness))
        fp.write('# --scale_z        : %.*f\n' % (args.decimals, args.scale_z))
        fp.write('# . tangentAngle   : %.*f [deg]\n' % (args.decimals, tangentAngle))
        fp.write('# . tangentLength  : %.*f\n' % (args.decimals, tangentLength))
        fp.write('# --rear_arc_x     : %.*f\n' % (args.decimals, args.rear_arc_x))
        fp.write('# --rear_width_z   : %.*f\n' % (args.decimals, args.rear_width_z))
        fp.write('# --exponent_width : %.*f\n' % (args.decimals, args.exponent_width))
        fp.write('# --wing_twist_z   : %.*f\n' % (args.decimals, args.wing_twist_z))
        fp.write('# . twistAngle     : %.*f [deg]\n' % (args.decimals, np.rad2deg(twistAngle)))
        fp.write('# --tx             : %.*f\n' % (args.decimals, args.tx))
        fp.write('# --ty             : %.*f\n' % (args.decimals, args.ty))
        fp.write('# --tz             : %.*f\n' % (args.decimals, args.tz))
        fp.write('# --xn             : %s\n' % args.xn)
        fp.write('# --xa             : %s\n' % args.xa)
        fp.write('# --xfit           : %s\n' % args.xfit)
        # Write file type
        fp.write('sketch\n')
        # Write units
        fp.write(unit + '\n')
        # Write plane normal (= y for XZ plane) and offset (= ty)
        fp.write(profileNormal + ', ' + str(ty) + '\n')
        # Write wing top points with spline
        fp.write('spline\n')
        for i in range(N_top):
            x = wing_spline[i][0]
            z = wing_spline[i][1]
            if i == N_top - 1 and tangentAngle != 0:
                # front edge point
                fp.write('%.*f, %.*f, %.*f, %.*f\n' % (args.decimals, x,
                                                       args.decimals, z,
                                                       args.decimals, tangentAngle,
                                                       args.decimals, tangentLength))
            else:
                # remaining points
                fp.write('%.*f, %.*f\n' % (args.decimals, x, args.decimals, z))
        # Write wing bottom points with spline
        # . same tangentAngle, because bottom profile has +180, but bottom spline
        #   has opposite orientation, so again +180.
        fp.write('spline\n')
        for i in range(N_top, N_top + N_bottom):
            x = wing_spline[i][0]
            z = wing_spline[i][1]
            if i == N_top:
                # front edge point
                fp.write('%.*f, %.*f, %.*f, %.*f\n' % (args.decimals, x,
                                                       args.decimals, z,
                                                       args.decimals, tangentAngle,
                                                       args.decimals, tangentLength))
            else:
                # remaining points
                fp.write('%.*f, %.*f\n' % (args.decimals, x, args.decimals, z))
        if args.rear_width_z > 0:
            if args.rear_arc_x:
                # Close rear edge points with arc
                fp.write('arc\n')
                xEnd = wing_spline[0][0]
                zEnd = wing_spline[0][1]
                xStart = wing_spline[-1][0]
                zStart = wing_spline[-1][1]
                # . Tune arc to be near tangent to profile
                xCurve = xEnd + args.rear_arc_x
                zCurve = (zEnd + zStart) / 2
                fp.write('%.*f, %.*f, %.*f, %.*f, %.*f, %.*f\n' % (args.decimals, xStart, args.decimals, zStart,
                                                                   args.decimals, xCurve, args.decimals, zCurve,
                                                                   args.decimals, xEnd, args.decimals, zEnd))
            else:
                # Close rear edge points with line
                fp.write('line\n')
                x = wing_spline[0][0]
                z = wing_spline[0][1]
                fp.write('%.*f, %.*f\n' % (args.decimals, x, args.decimals, z))
                x = wing_spline[-1][0]
                z = wing_spline[-1][1]
                fp.write('%.*f, %.*f\n' % (args.decimals, x, args.decimals, z))


if __name__ == '__main__':
    import sys
    import os
    import os.path
    import argparse
    import matplotlib.pyplot as plt

    ############################################################################
    # Parse arguments
    _parser = argparse.ArgumentParser('airfoils')
    _parser.add_argument('--folder', default='csv/', type=str, help='Wing profiles folder name')
    _parser.add_argument('--profile', default='NACA', type=str, help='Wing profile prefix name')
    _parser.add_argument('-M', default=1, type=int, help='NACA first digit, maximum camber')
    _parser.add_argument('-P', default=4, type=int, help='NACA second digit, location of maximum camber')
    _parser.add_argument('-T', default=8, type=int,
                         help='NACA last two digits, maximum thickness as a fraction of the chord')

    _parser.add_argument('--chord_len', default=1.0, type=float, help='Chord length in mm.')
    _parser.add_argument('--xn', default='', type=str, help='normalized x coordinates for profile')
    _parser.add_argument('--xa', default='', type=str, help='extra absolute x coordinates for profile in csv file')
    _parser.add_argument('--xfit', default=False, action='store_true',
                         help='When True then iterate to match exact x coordinates.')
    _parser.add_argument('--scale_z', default=1.0, type=float, help='Scale factor for profile thickness.')
    _parser.add_argument('--tangent_angle', default=-90.0, type=float, help='Tangent angle for front point of spline.')
    _parser.add_argument('--tangent_length', default=0.0, type=float, help='Tangent length for front point of spline.')
    _parser.add_argument('--rear_arc_x', default=0.0, type=float,
                         help='When > 0 then close rear edge with arc, when 0 with line.')
    _parser.add_argument('--rear_width_z', default=0.0, type=float, help='Rear edge width in mm.')
    _parser.add_argument('--exponent_width', default=4.0, type=float, help='Rear edge width power shape, 1 for linear.')
    _parser.add_argument('--wing_twist_z', default=0.0, type=float,
                         help='Rear edge twist in mm to make wing twist angle.')
    _parser.add_argument('--tx', default=0.0, type=float, help='Translate profile in x direction in mm.')
    _parser.add_argument('--ty', default=0.0, type=float, help='Translate profile in y direction in mm.')
    _parser.add_argument('--tz', default=0.0, type=float, help='Translate profile in z direction in mm.')
    _parser.add_argument('--decimals', default=2, type=int, help='Round profile values to number of decimals in mm.')
    _parser.add_argument('--plot', default=False, action='store_true', help='When True then plot profiles.')
    args = _parser.parse_args()

    tangentAngle = args.tangent_angle
    tangentLength = args.tangent_length
    if int(tangentAngle) != 0:
        if int(tangentLength) == 0:
            if args.profile == 'NACA':
                tangentLength = args.chord_len * args.scale_z / 6.0  # appropriate value for NACA-1408
            elif args.profile == 'GOE-444':
                tangentLength = args.chord_len * args.scale_z / 13.0  # appropriate value for GOE-444
    twistAngle = calculate_twist_angle(args)

    xn = naca_four_digit.parse_range_string(args.xn)
    xa = naca_four_digit.parse_float_string(args.xa)
    if len(xa) > 0:
        xe = xa - args.tx
        xe = xe / args.chord_len
        if np.min(xe) <= 0 or np.max(xe) >= 1:
            sys.exit('Extra x coordinate out of range.')
        xn = naca_four_digit.remove_array_coordinates(xn, xe)
        xn = naca_four_digit.combine_array_coordinates(xn, xe)

    # Select wing profile
    # . NACA four digit:
    #   - M first digit, m = M / 100 defines the maximum amount of camber
    #   - P second digit, p = P / 10 is the location of maximum camber from the
    #       front edge as a fraction of the chord length
    #   - T last two digits, t = T / 100 is the maximum thickness as a fraction
    #       of the chord length
    if args.profile == 'NACA':
        wingProfilesTuple, wingOffsetsTuple, wingParametersTuple = calculate_wing_naca(args)
    elif args.profile == 'GOE-444':
        wingProfilesTuple, wingOffsetsTuple, wingParametersTuple = calculate_wing_goe444(args)
    else:
        sys.exit('Unknown profile %s' % args.profile)
    profileBaseName = wingParametersTuple[0]
    thickness = wingParametersTuple[1]

    # Prepare folder for wing profiles
    folderName = os.path.normpath(args.folder)  # convert to path separators for local system
    folderName = os.path.join(folderName, profileBaseName)
    try:
        os.makedirs(folderName)
        print("Folder %s created!" % folderName)
    except FileExistsError:
        pass

    # Prepare for sketch in XZ plane
    profileName = profileBaseName
    # . add zx-plane at y offset in profile file name
    profileName += '_zx_y%d' % np.abs(args.ty)
    # . add profile chord_len in profile file name
    profileName += '_len%d' % args.chord_len
    # . y is normal of zx-plane
    profileNormal = 'y'

    ############################################################################
    # Wing profile
    wing_top_x, wing_top_z, wing_bottom_x, wing_bottom_z = wingProfilesTuple
    wing_top_offsets_z, wing_bottom_offsets_z = wingOffsetsTuple

    ############################################################################
    # Save profile in csv (comma seperated values) format
    filename = profileName + '.csv'
    filepathname = os.path.join(folderName, filename)
    wingProfilesTuple = (wing_top_x, wing_top_z, wing_bottom_x, wing_bottom_z)
    wingParametersTuple = (unit, profileBaseName, profileNormal, thickness, tangentAngle, twistAngle)

    save_csv_wing_profile(args, filepathname, wingProfilesTuple, wingParametersTuple)

    ############################################################################
    # Plot
    if args.plot:
        plt.figure(1)
        plt.title(profileBaseName + ', with %4.2f degrees twist' % np.degrees(twistAngle))
        plt.plot(wing_top_x, wing_top_z, 'r', wing_top_x, wing_top_z, 'ro',
                 wing_bottom_x, wing_bottom_z, 'b', wing_bottom_x, wing_bottom_z, 'bo')
        plt.legend(('top', 'bottom', 'thickness'), loc='best')
        plt.xlabel('x in mm')
        plt.ylabel('z in mm')
        plt.axis('equal')
        plt.grid()

        plt.figure(2)
        plt.title(profileBaseName + ', thickness')
        plt.plot((wing_top_x + wing_bottom_x)/2, wing_top_z - wing_bottom_z, '--g')
        plt.xlabel('x in mm')
        plt.ylabel('z in mm')
        plt.grid()

        plt.figure(3)
        plt.title(profileBaseName + ', rear_edge offsets_z')
        plt.plot(wing_top_x, wing_top_offsets_z, '--g',
                 wing_bottom_x, wing_bottom_offsets_z, '--b')
        plt.grid()

        plt.show()
