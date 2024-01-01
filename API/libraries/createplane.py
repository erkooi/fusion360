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
"""Module to create a plane in Fusion360 from three points defined in a csv
   file.

See schemacsv360.py for coordinates and plane definitions.

Plane CSV file format:
. comment lines or comment in line will be removed
. first line: 'plane' as filetype
. second line: resolution 'mm' or 'cm'
. next line: first point coordinates x, y, z
. next line: second point coordinates x, y, z
. next line: third point coordinates x, y, z
"""

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
    . threePoint3Ds: list of three point3D objects that define a plane

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
        elif li == 1:
            # Read units
            result, scale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        elif li <= 4:
            # Read the three points
            result, point3d = schemacsv360.get_3d_point(ui, title, filename, scale, lineArr)
            if not result:
                return resultFalse
            threePoint3Ds.append(point3d)
        else:
            # Too many lines in file
            return resultFalse

    # Successfully reached end of file
    return (True, threePoint3Ds)


def create_three_point_plane(hostComponent, planeName, threePoint3Ds):
    """Create plane through three points in threePoint3Ds.

    The three points have to be real objects in the hostComponent like a
    sketchPoint, instead of base objects like point3D or vector3D. Therefore
    first create three planes and sketches to define the three sketchPoints
    for the three 3D points in threePoint3Ds.

    Input:
    . hostComponent: place the plane in hostComponent Construction folder.
    . planeName: name for the plane
    . threePoint3Ds: list of three point3D objects that define a plane
    Return:
    . plane: plane object
    """
    # Create sketch points for the threePoint3Ds
    threeSketchPoints = []
    for pIndex, p3D in enumerate(threePoint3Ds):
        # Create offset normal plane for each point:
        # . choose 'x' as planeNormal,
        # . use x coordinate as plane offset,
        # . x, y, z coordinates become -z, y, 0 in offset normal plane, as
        #   explained for get_3d_point_in_offset_plane() in schemacsv360.py
        name = planeName + '_point_' + str(pIndex)
        offsetPlane = schemacsv360.create_offset_normal_plane(hostComponent, name, 'x', p3D.x)
        offsetPlane.isLightBulbOn = False
        # Create auxiliary sketch for each point
        sketch = utilities360.create_sketch_in_plane(hostComponent, name, offsetPlane)
        sketch.isLightBulbOn = False
        # Create auxiliary sketch point
        point = p3D
        point.x = -p3D.z
        point.y = p3D.y
        point.z = 0
        sketchPoints = sketch.sketchPoints
        sketchPoint = sketchPoints.add(point)
        threeSketchPoints.append(sketchPoint)

    # Get construction planes
    planes = hostComponent.constructionPlanes
    # Create construction plane input
    planeInput = planes.createInput()
    # Add construction plane by three points
    planeInput.setByThreePoints(threeSketchPoints[0], threeSketchPoints[1], threeSketchPoints[2])
    plane = planes.add(planeInput)
    plane.name = planeName
    plane.isLightBulbOn = True
    # Hide auxiliary Sketches folder
    hostComponent.isSketchFolderLightBulbOn = False
    # Show Construction folder with planes
    hostComponent.isConstructionFolderLightBulbOn = True
    return plane


def create_plane_from_csv_file(ui, title, filename, hostComponent):
    """Create plane from CSV file, in hostComponent Construction folder in Fusion360

    Input:
    . filename: full path and name of CSV file
    . hostComponent: place the plane in hostComponent Construction folder.
    Return:
    . result: True when valid plane, else False with None
    . plane: plane object

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, threePoint3Ds = parse_csv_plane_file(ui, title, filename)
    if not result:
        return (False, None)

    # Use stripped filename as plane name
    objectName = interfacefiles.extract_object_name(filename)

    # Create plane if there are valid points
    if len(threePoint3Ds) == 3:
        # Create plane in hostComponent
        plane = create_three_point_plane(hostComponent, objectName, threePoint3Ds)
    else:
        ui.messageBox('No valid points in %s' % filename, title)
        return (False, None)
    interface360.print_text(ui, 'Created plane for ' + filename)
    return (True, plane)


def create_planes_from_csv_files(ui, title, folderName, hostComponent):
    """Create planes from CSV files in folder, in hostComponent Construction
    folder in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: place the plane in hostComponent Construction folder.
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
