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

Define airfoil coordinates (in mm) in xz-plane.

- chord_len = chord length of profile.
- edge_width = z-thickness of the wing rear edge. Applied by adding a
    linearly increasing z-offset from 0 at front edge to edge_width at rear
    edge. Separate for top and bottom profile, so rear edge width = 2 *
    edge_width.
- edge_twist = rear edge z-offset. Using same read edge offset causes that
    the wing profile gets rotated along frint edge. The rotation increases
    towards the wing tip, because the wing chord length decreases towards the
    wing tip.
- tx = x-offset for profile. To place wing at build location of fuselage.
- tz = z-offset for profile. To place wing at build location of fuselage.
- decimals = 2, for 0.01 mm accuracy in rounded airfoil profile coordinates.

Usage:
# on command line
>   D:
>   cd "git\\<script dir>"
# or:
> cd /d/git/<script dir>
> python airfoils.py --chord_len 477 --edge_width 0.8 --edge_twist 4 --tx 746 --ty -175 --tz 19
> python airfoils.py --chord_len 441 --edge_width 0.8 --edge_twist 4 --tx 772 --ty -213 --tz 19
> python airfoils.py --chord_len 407 --edge_width 0.8 --edge_twist 4 --tx 797 --ty -250 --tz 19
> python airfoils.py --chord_len 152 --edge_width 0.8 --edge_twist 4 --tx 983 --ty -526 --tz 19

# in iPython:
import os
filepath='D:\\git\\<script dir>'
os.chdir(filepath)
run airfols.py

"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
import os
import os.path

################################################################################
# Right-handed coordinates X, Y, Z:
# . right hand fingers point from X to Y points tumb to Z
# . screw from X to Y goes to Z
#
#     z
#     |          . angleYZ
#     |--- y     . angleZX
#    /           . angleXY
#   x

################################################################################
# Constants
unit = 'mm'  # input in mm and output csv in mm


################################################################################
# Functions
def Rxz(angle):
    """ Rotate from x to z. """
    co, si = np.cos(angle), np.sin(angle)
    return np.array([[co, -si],
                     [si, co]])


################################################################################
# Parse arguments
_parser = argparse.ArgumentParser('airfoils')
_parser.add_argument('--folder', default='csv/NACA-1408', type=str, help='Wing profiles folder name')
_parser.add_argument('--profile', default='NACA-1408', type=str, help='Wing profile prefix name')
_parser.add_argument('--chord_len', default=1.0, type=float, help='Chord length in mm.')
_parser.add_argument('--scale_z', default=1.0, type=float, help='Scale factor for profile thickness.')
_parser.add_argument('--edge_width_z', default=0.0, type=float, help='Rear edge width in mm.')
_parser.add_argument('--edge_twist_z', default=0.0, type=float, help='Rear edge twist in mm to make wing twist.')
_parser.add_argument('--tx', default=0.0, type=float, help='Translate profile in x direction in mm.')
_parser.add_argument('--ty', default=0.0, type=float, help='Translate profile in y direction in mm.')
_parser.add_argument('--tz', default=0.0, type=float, help='Translate profile in z direction in mm.')
_parser.add_argument('--decimals', default=2, type=int, help='Round profile values to number of decimals in mm.')
args = _parser.parse_args()

folderName = os.path.normpath(args.folder)  # convert to path separators for local system
try:
    os.makedirs(folderName)
    print("Folder %s created!" % folderName)
except FileExistsError:
    pass

chord_len = args.chord_len
edge_width_z = args.edge_width_z
edge_twist_z = args.edge_twist_z
tx = args.tx
ty = args.ty
tz = args.tz


################################################################################
# Wing profiles in zx-plane
# . x = 0 is front edge
# . x = 1 is rear edge
# . y < 0 is left wing
# . z > 0 is top of wing

# NACA-1408
naca_1408_top_x = np.flip(np.array(
                  [1.00000, 0.95016, 0.90027, 0.80039, 0.70041,
                   0.60034, 0.50020, 0.40000, 0.29950, 0.24926,
                   0.19904, 0.14889, 0.09883, 0.07386, 0.04896,
                   0.02418, 0.01189, 0.00000]))

naca_1408_top_z = np.flip(np.array(
                  [0.00084, 0.00698, 0.01271, 0.02305, 0.03193,
                   0.03931, 0.04502, 0.04869, 0.04939, 0.04819,
                   0.04574, 0.04171, 0.03558, 0.03138, 0.02602,
                   0.01862, 0.01324, 0.00000]))

naca_1408_bottom_x = np.array(
                     [0.00000, 0.01311, 0.02582, 0.05104, 0.07614,
                      0.10117, 0.15111, 0.20096, 0.25074, 0.30050,
                      0.40000, 0.49980, 0.59966, 0.69959, 0.79961,
                      0.89973, 0.94984, 1.00000])

naca_1408_bottom_z = np.array(
                     [0.00000, -0.01200, -0.01620, -0.02134, -0.02458,
                      -0.02682, -0.02953, -0.03074, -0.03101, -0.03063,
                      -0.02869, -0.02556, -0.02153, -0.01693, -0.01193,
                      -0.00659, -0.00378, -0.00084])

# GOE-444
goe_444_x = np.array(
            [0.0000000, 0.0125000, 0.0250000, 0.0500000, 0.0750000,
             0.1000000, 0.1500000, 0.2000000, 0.3000000, 0.4000000,
             0.5000000, 0.6000000, 0.7000000, 0.8000000, 0.9000000,
             0.9500000, 1.0000000])

goe_444_z = np.array(
            [0.0000000, 0.0060000, 0.0090000, 0.0130000, 0.0160000,
             0.0190000, 0.0230000, 0.0255000, 0.0280000, 0.0280000,
             0.0270000, 0.0240000, 0.0195000, 0.0140000, 0.0080000,
             0.0045000, 0.0000000])

# Select profile
profile_name = ''
if args.profile == 'NACA-1408':
    profile_name = 'NACA-1408'
    profile_top_x = naca_1408_top_x
    profile_top_z = naca_1408_top_z
    profile_bottom_x = naca_1408_bottom_x
    profile_bottom_z = naca_1408_bottom_z
if args.profile == 'GOE-444':
    profile_name = 'GOE-444'
    profile_top_x = goe_444_x
    profile_top_z = goe_444_z
    profile_bottom_x = goe_444_x
    profile_bottom_z = -1 * goe_444_z

profile_name += '_zx'  # profile in zx-plane
profile_name += '_y%d' % np.abs(args.ty)

profile_normal = 'y'  # y is normal of zx-plane

wing_top_x = np.copy(profile_top_x)
wing_top_z = np.copy(profile_top_z)
wing_bottom_x = np.copy(profile_bottom_x)
wing_bottom_z = np.copy(profile_bottom_z)

################################################################################
# Calculate profile

# Apply chord_len, args.scale_z
wing_top_x *= chord_len
wing_top_z *= chord_len * args.scale_z
wing_bottom_x *= chord_len
wing_bottom_z *= chord_len * args.scale_z

# Apply edge_width_z by applying linear offsets_z along x chord line
# . top
edge_width = wing_top_z[-1]
offset_width = edge_width_z - edge_width
offsets_z = offset_width * profile_top_x
wing_top_z += offsets_z
# . bottom
edge_width = wing_bottom_z[-1]
offset_width = -1 * edge_width_z - edge_width
offsets_z = offset_width * profile_bottom_x
wing_bottom_z += offsets_z

# Apply edge_twist_z
twist_angle = np.arctan2(edge_twist_z, chord_len)
# . top
xx = np.zeros(wing_top_x.size)
zz = np.zeros(wing_top_z.size)
i = 0
for x, z in zip(wing_top_x, wing_top_z):
    v = Rxz(twist_angle) @ np.array([x, z])
    xx[i] = v[0]
    zz[i] = v[1]
    i += 1
wing_top_x = xx
wing_top_z = zz

# . bottom
xx = np.zeros(wing_bottom_x.size)
zz = np.zeros(wing_bottom_z.size)
i = 0
for x, z in zip(wing_bottom_x, wing_bottom_z):
    v = Rxz(twist_angle) @ np.array([x, z])
    xx[i] = v[0]
    zz[i] = v[1]
    i += 1
wing_bottom_x = xx
wing_bottom_z = zz

# Keep wing edge at chord_len
wing_top_x[-1] = chord_len
wing_bottom_x[-1] = chord_len

# Apply tx, tz
wing_top_x += tx
wing_top_z += tz
wing_bottom_x += tx
wing_bottom_z += tz


################################################################################
# Round values
decimals = args.decimals  # default resolution 0.1 mm
wing_top_x = np.round(wing_top_x, decimals=decimals)
wing_top_z = np.round(wing_top_z, decimals=decimals)
wing_bottom_x = np.round(wing_bottom_x, decimals=decimals)
wing_bottom_z = np.round(wing_bottom_z, decimals=decimals)
y_offset = np.round(ty, decimals=decimals)

################################################################################
# Save profile in csv (comma seperated values) format
N = wing_top_x.size + wing_bottom_x.size - 1
wing_spline = np.zeros((N, 2))
i = 0
for x, z in zip(np.flip(wing_top_x), np.flip(wing_top_z)):
    wing_spline[i][0] = x
    wing_spline[i][1] = z
    i += 1
j = 0
for x, z in zip(wing_bottom_x, wing_bottom_z):
    # skip x = 0 coordinate, because it is same as in wing_top_x
    if j > 0:
        wing_spline[i][0] = x
        wing_spline[i][1] = z
        i += 1
    j += 1

filename = profile_name + '.csv'
filepathname = os.path.join(folderName, filename)
with open(filepathname, 'w') as fp:
    # Write file type
    fp.write('sketch\n')
    # Write units
    fp.write(unit + '\n')
    # Write plane normal and offset
    fp.write(profile_normal + ', ' + str(y_offset) + '\n')
    # Write wing points with spline
    fp.write('spline\n')
    for i in range(N):
        x = wing_spline[i][0]
        y = wing_spline[i][1]
        fp.write('%.*f, %.*f\n' % (decimals, x, decimals, y))
    # Close edge points with line
    fp.write('line\n')
    x = wing_spline[0][0]
    y = wing_spline[0][1]
    fp.write('%.*f, %.*f\n' % (decimals, x, decimals, y))
    x = wing_spline[-1][0]
    y = wing_spline[-1][1]
    fp.write('%.*f, %.*f\n' % (decimals, x, decimals, y))

################################################################################
# Plot
plt.figure(1)
plt.title(profile_name + ', with %4.2f degrees twist' % np.degrees(twist_angle))
plt.plot(wing_top_x, wing_top_z, 'r', wing_bottom_x, wing_bottom_z, 'b')
plt.legend(('top', 'bottom', 'thickness'), loc='best')
plt.xlabel('x in mm')
plt.ylabel('z in mm')
plt.axis('equal')
plt.grid()

plt.figure(2)
plt.title(profile_name + ', thickness')
plt.plot((wing_top_x + wing_bottom_x)/2, wing_top_z - wing_bottom_z, '--g')
plt.xlabel('x in mm')
plt.ylabel('z in mm')
plt.grid()

plt.show()
