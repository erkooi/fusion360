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
# Date: 31 may 2023
#
# References:
# [1] https://forums.autodesk.com/t5/fusion-360-api-and-scripts/sketchpoint-coordinate-with-too-many-decimals-for-plane/m-p/12521506#M20779  # noqa: E501

"""Module to create a plane in Fusion360 from three points defined in a csv
   file.

See schemacsv360.py for coordinates and plane definitions.

Plane CSV file format:
. comment lines or comment in line will be removed
. first line: 'plane' as filetype, name of the plane, name of the group
  component for the plane.
. second line: resolution 'mm' or 'cm'
. next line: 'point', first point coordinates x, y, z
. next line: 'point', second point coordinates x, y, z
. next line: 'point', third point coordinates x, y, z
"""

import adsk.core
import interfacefiles
import interface360
import utilities360
import schemacsv360


def parse_csv_plane_file(ui, title, filename):
    """Parse plane CSV file.

    Reads three points that define plane from csv file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid threePoint3Ds, else False with None
    . planeTuple:
      - planeName: name of the plane object
      - groupComponentName: group component for the plane object
      - threePoint3Ds: list of three point3D objects that define a plane

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for plane
    resultFalse = (False, None)
    threePoint3Ds = []
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            # Read file type
            if lineWord != 'plane':
                return resultFalse
            planeName = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
        elif li == 1:
            # Read units
            result, scale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        elif li <= 4:
            if lineWord != 'point':
                return resultFalse
            # Read the three points
            result, point3d = schemacsv360.get_3d_point(ui, title, filename, scale, lineArr[1:])
            if not result:
                return resultFalse
            threePoint3Ds.append(point3d)
        else:
            # Too many lines in file
            return resultFalse

    # Successfully reached end of file
    planeTuple = (planeName, groupComponentName, threePoint3Ds)
    return (True, planeTuple)


# The _create_three_points_in_separate_sketches() fails if the three points
# happen to project on a line in the z = 0 plane. This is a bug in Fusion360,
# as reported in [1]. The work around solution is to instead use
# _create_three_points_in_one_sketch(), that defines all three points in one
# sketch. This is possible, because it is allowed to use z != 0 in a sketch,
# even though the sketch is like 2D. Explanation by Brian Ekins in [1]:
# . Sketches are 3D, but in the GUI, they mostly behave like 2D, where the
#   geometry you sketch lies on the X-Y plane. When a sketch is active, there
#   is an option in the SKETCH PALETTE dialog for "3D Sketch". When it is
#   checked, you have some additional capabilities to sketch in 3 dimensions.
#   This doesn't change the sketch itself, but just the GUI to make it easier
#   to draw in 3D. Another way to see this is to draw geometry on the X-Y plane
#   and then use the Move command to move sketch geometry out of the X-Y plane.
def _create_three_points_in_separate_sketches(ui, groupComponent, planeName, threePoint3Ds):
    """Create three points in separate sketches.

    Input:
    . groupComponent: place the plane in groupComponent Construction folder.
    . planeName: name prefix for the offset planes and sketches
    . threePoint3Ds: list of three point3D objects that define a plane
    Return:
    . threeSketchPoints: list with three sketch points that can define a plane

    Uses ui to report faults via Fusion360 GUI.
    """
    threeSketchPoints = []
    for pIndex, p3D in enumerate(threePoint3Ds):
        # Create a separate offset normal plane for each point:
        # . choose 'x' as planeNormal,
        # . use x coordinate as plane offset,
        # . x, y, z coordinates become -z, y, 0 in offset normal plane, as
        #   explained for get_3d_point_in_offset_plane() in schemacsv360.py
        name = planeName + '_point_' + str(pIndex)
        offsetPlane = schemacsv360.create_offset_normal_plane(groupComponent, name, 'x', p3D.x)
        offsetPlane.isLightBulbOn = False
        # Create a separate auxiliary sketch for each point
        sketch = utilities360.create_sketch_in_plane(groupComponent, name, offsetPlane)
        sketch.isLightBulbOn = False
        # Create auxiliary sketch point
        point = adsk.core.Point3D.create(-p3D.z, p3D.y, 0)
        sketchPoints = sketch.sketchPoints
        sketchPoint = sketchPoints.add(point)
        # interface360.print_text(ui, 'sketchPoint (x, y, z) = ' +
        #                         interfacefiles.value_to_str(sketchPoint.worldGeometry.x) + ', ' +
        #                         interfacefiles.value_to_str(sketchPoint.worldGeometry.y) + ', ' +
        #                         interfacefiles.value_to_str(sketchPoint.worldGeometry.z))
        threeSketchPoints.append(sketchPoint)
    return threeSketchPoints


def _create_three_points_in_one_sketch(ui, groupComponent, sketchName, threePoint3Ds):
    """Create three points in one 3D sketch in the yZ origin plane.

    Input:
    . groupComponent: place the plane in groupComponent Construction folder.
    . sketchName: name prefix for the sketch in the origin plane
    . threePoint3Ds: list of three point3D objects that define a plane
    Return:
    . threeSketchPoints: list with three sketch points that can define a plane

    Uses ui to report faults via Fusion360 GUI.
    """
    # Use one sketch:
    # . choose yZ as origin plane, so 'x' as plane normal,
    # . use x coordinate as z coordinate plane offset,
    # . x, y, z coordinates become -z, y, x in the yZ origin plane, as
    #   explained for get_3d_point_in_offset_plane() in schemacsv360.py
    originPlane = groupComponent.yZConstructionPlane

    # Create the one auxiliary sketch in the originPlane
    name = sketchName + '_three_points'
    sketch = utilities360.create_sketch_in_plane(groupComponent, name, originPlane)
    sketch.isLightBulbOn = False

    threeSketchPoints = []
    for pIndex, p3D in enumerate(threePoint3Ds):
        # Create auxiliary sketch point
        point = adsk.core.Point3D.create(-p3D.z, p3D.y, p3D.x)
        sketchPoints = sketch.sketchPoints
        sketchPoint = sketchPoints.add(point)
        # interface360.print_text(ui, 'sketchPoint (x, y, z) = ' +
        #                         interfacefiles.value_to_str(sketchPoint.worldGeometry.x) + ', ' +
        #                         interfacefiles.value_to_str(sketchPoint.worldGeometry.y) + ', ' +
        #                         interfacefiles.value_to_str(sketchPoint.worldGeometry.z))
        threeSketchPoints.append(sketchPoint)
    return threeSketchPoints


def create_three_point_plane(ui, groupComponent, planeName, threePoint3Ds):
    """Create plane through three points in threePoint3Ds.

    The three points have to be real objects in the groupComponent like a
    sketchPoint, instead of base objects like point3D or vector3D. Therefore
    first create three planes and sketches to define the three sketchPoints
    for the three 3D points in threePoint3Ds.

    Input:
    . groupComponent: place the plane in groupComponent Construction folder.
    . planeName: name for the plane
    . threePoint3Ds: list of three point3D objects that define a plane
    Return:
    . plane: plane object

    Uses ui to report faults via Fusion360 GUI.
    """
    # Create list of three sketch points for the threePoint3Ds
    # threeSketchPoints = _create_three_points_in_separate_sketches(ui, groupComponent, planeName, threePoint3Ds)
    threeSketchPoints = _create_three_points_in_one_sketch(ui, groupComponent, planeName, threePoint3Ds)

    # Get construction planes
    planes = groupComponent.constructionPlanes
    # Create construction plane input
    planeInput = planes.createInput()
    # Add construction plane by three points
    planeInput.setByThreePoints(threeSketchPoints[0], threeSketchPoints[1], threeSketchPoints[2])
    plane = planes.add(planeInput)
    plane.name = planeName
    plane.isLightBulbOn = True
    # Hide auxiliary Sketches folder
    groupComponent.isSketchFolderLightBulbOn = False
    # Show Construction folder with planes
    groupComponent.isConstructionFolderLightBulbOn = True
    return plane


def create_plane_from_csv_file(ui, title, filename, hostComponent):
    """Create plane from CSV file, in Fusion360

    Dependent on the groupComponentName the plane will be put in the
    Construction folder of hostComponent or hostComponent/groupComponent.

    Input:
    . filename: full path and name of CSV file
    . hostComponent: host component for the plane
    Return:
    . result: True when valid plane, else False with None
    . plane: plane object

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, planeTuple = parse_csv_plane_file(ui, title, filename)
    if not result:
        return (False, None)
    planeName, groupComponentName, threePoint3Ds = planeTuple

    # Create plane if there are valid points
    if len(threePoint3Ds) == 3:
        # Create groupComponent in hostComponent for plane object, if it does
        # not already exist, else use hostComponent if groupComponentName is
        # empty string or is the hostComponent.
        groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)
        # Create plane in groupComponent
        plane = create_three_point_plane(ui, groupComponent, planeName, threePoint3Ds)
    else:
        ui.messageBox('No valid points in %s' % filename, title)
        return (False, None)
    interface360.print_text(ui, 'Created plane for ' + filename)
    return (True, plane)


def create_planes_from_csv_files(ui, title, folderName, hostComponent):
    """Create planes from CSV files in folder, in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: host component for the planes
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)
    if len(filenames) > 0:
        for filename in filenames:
            # Create plane from CSV file in hostComponent
            result, plane = create_plane_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No plane CSV files in %s' % folderName, title)
