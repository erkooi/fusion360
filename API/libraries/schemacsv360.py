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
# Author: Eric Kooistra.
# Date: 1 jun 2023
"""Module with utilities to represent items defined in CSV schema file in Fusion360.

Use right-handed coordinates X, Y, Z:

    z
    |          . positive angle YZ, planeNormal = 'x'
    |--- y     . positive angle ZX, planeNormal = 'y'
   /           . positive angle XY, planeNormal = 'z'
  x

Offset plane with rerspect to normal origin plane YZ, ZX or XY.

Use user unit 'mm' or 'cm' in CSV file, automatically scale to cm because
Fusion360 API uses cm unit.
"""

import adsk.core
import math

validUnits = ['mm', 'cm']
validPlaneNormals = ['x', 'y', 'z']


def read_units(ui, title, filename, fLine):
    """Read unit from file fLine.

    Input:
    . fLine: 'mm' or 'cm', spaces are stripped
    Return:
    . result: True when valid, else False
    . scale: scale factor with respect to API cm unit

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    result = (False, None)
    unitStr = fLine.strip()
    if unitStr in validUnits:
        # Scale user units to cm unit used by API
        scale = 1
        if unitStr == 'mm':
            scale = 0.1
        result = (True, scale)
    if not result[0]:
        ui.messageBox('No valid unit %s in %s' % (unitStr, filename), title)
    return result


def read_offset_plane(ui, title, filename, fLine, scale):
    """Read normal axis and offset of the offset plane from file fLine.

    Input:
    . fLine: planeNormal (= 'x', 'y' or 'z'), planeOffset (= float value)
    . scale: scale factor between dataArr unit and API cm unit
    Return:
    . result: True when valid, else False
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . planeOffset: offset from origin plane

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    entries = fLine.split(',')
    entries = [e.strip() for e in entries]
    result = (False, None, None)
    if len(entries) == 2:
        # Get plane normal
        planeNormal = entries[0]
        if planeNormal in validPlaneNormals:
            # Get plane offset
            try:
                planeOffset = float(entries[1]) * scale
                result = (True, planeNormal, planeOffset)
            except Exception:
                pass
    if not result[0]:
        ui.messageBox('No valid plane %s of %s' % (fLine, filename), title)
    return result


def get_3d_point(ui, title, filename, dataArr, scale):
    """Get 3D point x, y, z coordinates.

    Input:
    . dataArr: 3D point
        [0] = x coordinate
        [1] = y coordinate
        [3] = z coordinate
    . scale: scale factor between dataArr unit and API cm unit
    Return:
    . result: True when valid, else False
    . point3D: point3D object

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    try:
        # Get point3D
        x = float(dataArr[0]) * scale
        y = float(dataArr[1]) * scale
        z = float(dataArr[2]) * scale
        point3D = adsk.core.Point3D.create(x, y, z)
        result = (True, point3D)
    except Exception:
        ui.messageBox('No valid 3D point in %s of %s' % (dataArr, filename), title)
        result = (False, None)
    return result


def create_plane_vector3D(planeNormal, ampl, angle):
    """Create vector3D in plane with coordinates (a, b, 0) for input amplitude
    and angle.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . ampl: amplitude value of vector with  respect to plane origin
    . angle: angle value in radians of vector with  respect to plane origin
    Return:
    . vector3D: vector3D object
    """
    a = ampl * math.cos(angle)
    b = ampl * math.sin(angle)
    if planeNormal == 'x':  # yz-plane
        # sketch.xDirection.asArray() = [0, 0,-1]
        # sketch.yDirection.asArray() = [0, 1, 0]
        vector3D = adsk.core.Vector3D.create(-b, a, 0)
    elif planeNormal == 'y':  # zx-plane, so -y for xz-plane
        # sketch.xDirection.asArray() = [1, 0, 0]
        # sketch.yDirection.asArray() = [0, 0,-1]
        vector3D = adsk.core.Vector3D.create(a, -b, 0)
    elif planeNormal == 'z':  # xy-plane
        # sketch.xDirection.asArray() = [1, 0, 0]
        # sketch.yDirection.asArray() = [0, 1, 0]
        vector3D = adsk.core.Vector3D.create(a, b, 0)
    return vector3D


def create_offset_normal_plane(component, planeName, planeNormal, planeOffset):
    """Create plane in component, at offset of normal origin plane.

    Input:
    . component: place the sketch in component.
    . planeName: name for the offset plane
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . planeOffset: offset from origin plane
    Return:
    . offsetPlane: plane object
    """
    # Determine origin plane
    if planeNormal == 'x':  # x-normal of yz-plane
        originPlane = component.yZConstructionPlane
    elif planeNormal == 'y':  # y-normal of zx-plane
        originPlane = component.xZConstructionPlane
    elif planeNormal == 'z':  # z-normal of xy-plane
        originPlane = component.xYConstructionPlane
    # Determine offset plane
    if planeOffset == 0:
        offsetPlane = originPlane
    else:
        # Get construction planes
        planes = component.constructionPlanes
        # Create construction plane input
        planeInput = planes.createInput()
        # Add construction plane by offset
        offsetValue = adsk.core.ValueInput.createByReal(planeOffset)
        planeInput.setByOffset(originPlane, offsetValue)
        offsetPlane = planes.add(planeInput)
        offsetPlane.name = planeName
        # Hide Construction folder with planes
        component.isConstructionFolderLightBulbOn = False
    return offsetPlane
