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
# Date: 12 mar 2023
"""Module to import line segments from csv file into a sketch in Fusion360.

See schemacsv360.py for coordinates and plane definitions. Only sketches on
planes that are parallel to the origin planes (xy, yz, and zx) are supported.

Sketch CSV file format:
. no comment lines or comment in line
. first line: 'sketch' as filetype
. second line: resolution 'mm' or 'cm'
. next line: plane normal axis 'x', 'y' or 'z', plane offset value
  - normal 'x': yz-plane
  - normal 'y': zx-plane
  - normal 'z': xy-plane
. loop segments:
  - next line: segment type 'spline', 'line, 'offset_curve'
  - next lines: list of two or more 2D point coordinates in sketch plane
    . per 2D point x, y coordinates, optional spline handle angle in degrees
      and spline length
  - with offset_curve:
    . defines an offset curve for the previous segments
    . next line contains direction point (x, y) for offset direction and
      offset distance
. empty line ends file
"""

import adsk.core
import os.path
import math

import interfacefiles
import interface360
import utilities360
import schemacsv360

validSegmentTypes = ['spline', 'line', 'offset_curve']


def read_segment_type(ui, title, filename, lineWord):
    """Read segment type from file line.

    Input:
    . lineWord: word from file line
    Return:
    . result: True when valid segmentType, else False with None
    . segmentType: string in validSegmentTypes
    """
    segmentType = lineWord
    if segmentType not in validSegmentTypes:
        ui.messageBox('No valid segment type %s in %s' % (segmentType, filename), title)
        return (False, None)
    return (True, segmentType)


def get_segment_point(ui, title, filename, planeNormal, dataArr, scale):
    """Get 2D point in offset plane.

    Map yz, zx, xy 2D point in dataArr to xy point in offset plane with z = 0.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . dataArr: 2D point in offset plane
        [0] = x coordinate in offset plane
        [1] = y coordinate in offset plane
        Optional tangent at 2D spline point:
        [2] = angle in degrees of tangent handle at 2D spline point
        [3] = length of tangent handle at 2D spline point
    . scale: scale factor between dataArr unit and API cm unit
    Return:
    . result: True when valid pointTuple, else False with None
    . pointTuple:
      - point3D: point (x, y, z) coordinates in plane with z = 0.
      - tangent: optional tangent (angle, length) of spline at point3D.

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    try:
        # Get point3D in offset plane
        a = float(dataArr[0]) * scale
        b = float(dataArr[1]) * scale
        data2D = [0, 0]  # keep z = 0 in offset plane
        if planeNormal == 'x':  # yz-plane
            # sketch.xDirection.asArray() = [0, 0,-1]
            # sketch.yDirection.asArray() = [0, 1, 0]
            data2D[0] = -b
            data2D[1] = a
        elif planeNormal == 'y':  # zx-plane, so -y for xz-plane
            # sketch.xDirection.asArray() = [1, 0, 0]
            # sketch.yDirection.asArray() = [0, 0,-1]
            data2D[0] = a
            data2D[1] = -b
        elif planeNormal == 'z':  # xy-plane
            # sketch.xDirection.asArray() = [1, 0, 0]
            # sketch.yDirection.asArray() = [0, 1, 0]
            data2D[0] = a
            data2D[1] = b
        point3D = adsk.core.Point3D.create(data2D[0], data2D[1], 0)

        # Get optional point tangent angle and length
        angle = None
        if len(dataArr) > 2:
            angle = float(dataArr[2])
        length = None
        if len(dataArr) > 3:
            length = float(dataArr[3]) * scale
        if len(dataArr) > 4:
            raise Exception
        tangent = (angle, length)
        pointTuple = (point3D, tangent)
        result = (True, pointTuple)
    except Exception:
        ui.messageBox('No valid 2D point in %s of %s' % (dataArr, filename), title)
        result = (False, None)
    return result


def get_segment_offset(ui, title, filename, dataArr, scale):
    """Get offset parameters for offset_curve segment

    Input:
    . dataArr:
        [0] = x coordinate in plane, for offset direction of offset_curve
        [1] = y coordinate in plane, for offset direction of offset_curve
        [2] = offset distance
    . scale: scale factor between dataArr unit and API cm unit
    Return:
    . result: True when valid offsetTuple, else False with None
    . offsetTuple:
      - directionPoint3D: scaled offset coordinates in plane (x, y, 0)
      - offsetDistance: scaled offset distance

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    try:
        # Get point3D for offset direction of offset_curve in offset plane
        x = float(dataArr[0]) * scale
        y = float(dataArr[1]) * scale
        directionPoint3D = adsk.core.Point3D.create(x, y, 0)

        # Get offset distance for offset_curve
        offsetDistance = float(dataArr[2]) * scale
        offsetTuple = (directionPoint3D, offsetDistance)
        result = (True, offsetTuple)
    except Exception:
        ui.messageBox('No valid offset_curve parameters in %s of %s' % (dataArr, filename), title)
        result = (False, None)
    return result


def adjust_spline_tangents(ui, planeNormal, spline, segmentTangents):
    """Use segmentTangents to adjust the spline handles per spline point.

    The tangent in segmentTangent can adjust the angle, length of the handle
    of a spline point. If angle, length is None, then the default value for
    the handle is kept. The handle is adjusted by moving the end point to a
    new point that is located relative to the spline point by tangentVector3D.
    Fusion360 takes care that the handle remains centered at the spline point.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . spline: spline object from sketch.sketchCurves.sketchFittedSplines
    . segmentTangents: list of tangent (angle, length) for all spline.fitPoints
    Return: None

    Uses ui for interface360.print_text().
    """
    verbosity = False  # no print_text()

    # Get spline fit points
    fitSketchPoints = spline.fitPoints

    # Adjust or keep default tangent handle per spline point
    for fitSketchPoint, tangent in zip(fitSketchPoints, segmentTangents):
        # Get tangent angle from user
        tangentAngle = tangent[0]
        if tangentAngle is not None:
            interface360.print_text(ui, 'tangentAngle = ' + str(tangentAngle), verbosity)

            # Get handleSketchLine of spline point
            handleSketchLine = spline.activateTangentHandle(fitSketchPoint)  # is SketchLine

            # Get tangent length from user or default
            tangentLength = tangent[1]  # use length from user
            if tangentLength is None:
                tangentLength = handleSketchLine.length  # use default length of handleSketchLine
            interface360.print_text(ui, 'tangentLength = ' + str(tangentLength), verbosity)

            # Create tangent vector
            angle = math.radians(tangentAngle)
            ampl = tangentLength / 2
            tangentVector3D = schemacsv360.create_plane_vector3D(planeNormal, ampl, angle)
            interface360.print_text(ui, 'tangentVector3D' + str(tangentVector3D.asArray()), verbosity)  # = [x, y, z]

            # Get point of spline
            fitPoint3D = fitSketchPoint.geometry
            fitVector3D = fitPoint3D.asVector()
            interface360.print_text(ui, 'fitVector3D' + str(fitVector3D.asArray()), verbosity)  # = [x, y, z]

            # Get end point of the handleSketchLine
            handleSketchPoint = handleSketchLine.endSketchPoint
            handlePoint3D = handleSketchPoint.geometry
            handleVector3D = handlePoint3D.asVector()
            interface360.print_text(ui, 'handleVector3D' + str(handleVector3D.asArray()), verbosity)  # = [x, y, z]

            # Create end point for handle vector
            moveVector3D = tangentVector3D  # direction vector from fitPoint3D to new point
            moveVector3D.add(fitVector3D)  # pointing vector from origin to new point
            moveVector3D.subtract(handleVector3D)  # direction vector from handleVector3D to new point
            interface360.print_text(ui, 'moveVector3D' + str(moveVector3D.asArray()), verbosity)  # = [x, y, z]

            # Move the end point of the handle of the spline point
            handleSketchPoint.move(moveVector3D)


def parse_csv_sketch_file(ui, title, filename):
    """Parse sketch CSV file.

    Reads offset plane and sketch segments from a sketch CSV file.

    Input:
    . filename: full path and name of a sketch CSV file
    Return:
    . result: True when valid sketchTuple, else False with None
    . sketchTuple:
      - planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
      - planeOffset: offset from origin plane
      - segments: list of (segmentType, ... segment data ...>)

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read sketch CSV file and remove comments and empty lines
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for sketch sections
    resultFalse = (False, None)
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            # Read file type
            if lineWord != 'sketch':
                return resultFalse
        elif li == 1:
            # Read units
            result, scale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        elif li == 2:
            # Read plane normal axis and offset of the sketch plane from lineArr
            result, planeTuple = schemacsv360.read_offset_plane(ui, title, filename, lineArr, scale)
            if not result:
                return resultFalse
            planeNormal, planeOffset = planeTuple
            # Prepare list with sketch segment locations
            segmentType = ''
            segmentLocations = []
            liStart = li
            liLast = li
        else:
            # Locate sketch segments in fileLines
            if len(lineArr) == 1:
                # Append location and type of previous sketch segment
                if li > liStart + 1:
                    segmentLocations.append((liStart, liLast, segmentType))
                # Read new sketch segment type from file line
                result, segmentType = read_segment_type(ui, title, filename, lineWord)
                if not result:
                    return resultFalse
                liStart = li
            else:
                liLast = li
    # Append location and type of last sketch segment
    segmentLocations.append((liStart, liLast, segmentType))

    # Parse file lines for sketch segments
    segments = []
    for (liStart, liLast, segmentType) in segmentLocations:
        result = False
        if segmentType == 'spline':
            result, segmentTuple = parse_segment_spline(ui, title, filename, planeNormal, scale,
                                                        liStart, liLast, lineLists)
        elif segmentType == 'line':
            result, segmentTuple = parse_segment_line(ui, title, filename, planeNormal, scale,
                                                      liStart, liLast, lineLists)
        elif segmentType == 'offset_curve':
            result, segmentTuple = parse_segment_offset_curve(ui, title, filename, scale,
                                                              liStart, lineLists)
        if result:
            segments.append(segmentTuple)
        else:
            return resultFalse

    # Successfully reached end of file
    sketchTuple = (planeNormal, planeOffset, segments)
    return (True, sketchTuple)


def parse_segment_spline(ui, title, filename, planeNormal, scale, liStart, liLast, lineLists):
    """Parse spline segment section from file lines [liStart : liLast + 1] in
       lineLists.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . scale: scale factor between dataArr unit and API cm unit
    . liStart: file line index of segmentType 'spline' in lineLists, so file
        line at liStart + 1 contains the point data for the first spline point
    . liEnd: file line at liEnd index contains point data for the last spline
        point
    . lineLists: list of file line data lists
    Return:
    . result: True when valid segmentTuple, else False with None
    . segmentTuple:
      - segmentType: 'spline'
      - segmentPoints: array of point3D
      - segmentTangents: list of tangents (angle, length) per corresponding
        point3D in segmentPoints. If tangent = (None, None) then Fusion360 will
        define the tangent.

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    resultFalse = (False, None)
    lineNr = liStart + 1  # index starts at 0, nr starts at 1
    segmentPoints = adsk.core.ObjectCollection.create()
    segmentTangents = []
    # Check segment type
    segmentType = lineLists[liStart][0]
    if segmentType != 'spline':
        ui.messageBox('No spline segment in %s at line %d' % (filename, lineNr), title)
        return resultFalse
    # Check segment length
    if liLast - liStart < 2:
        ui.messageBox('Not enough points in segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Read 2D point in offset plane, one 2D point per file line
    for li in range(liStart + 1, liLast + 1):
        dataArr = lineLists[li]
        result, pointTuple = get_segment_point(ui, title, filename, planeNormal, dataArr, scale)
        if not result:
            return resultFalse
        point3D, tangent = pointTuple
        segmentPoints.add(point3D)
        segmentTangents.append(tangent)
    # Check segment length
    if segmentPoints.count < 2:
        ui.messageBox('Not enough points in segment in %s' % filename, title)
        return resultFalse
    segmentTuple = (segmentType, segmentPoints, segmentTangents)
    return (True, segmentTuple)


def parse_segment_line(ui, title, filename, planeNormal, scale, liStart, liLast, lineLists):
    """Parse line segment section from lines [liStart : liLast + 1] in
       lineLists.

    Same interface as parse_segment_spline(), but only with segmentPoints, so
    without segmentTangents.

    """
    resultFalse = (False, None)
    lineNr = liStart + 1  # index starts at 0, nr starts at 1
    segmentPoints = adsk.core.ObjectCollection.create()
    # Check segment type
    segmentType = lineLists[liStart][0]
    if segmentType != 'line':
        ui.messageBox('No line segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Check segment length
    if liLast - liStart < 2:
        ui.messageBox('Not enough points in segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Read 2D point in offset plane, one 2D point per file line
    for li in range(liStart + 1, liLast + 1):
        dataArr = lineLists[li]
        result, pointTuple = get_segment_point(ui, title, filename, planeNormal, dataArr, scale)
        if not result:
            return resultFalse
        point3D = pointTuple[0]
        segmentPoints.add(point3D)
    # Check segment length
    if segmentPoints.count < 2:
        ui.messageBox('Not enough points in segment in %s' % filename, title)
        return resultFalse
    segmentTuple = (segmentType, segmentPoints)
    return (True, segmentTuple)


def parse_segment_offset_curve(ui, title, filename, scale, liStart, lineLists):
    """Parse offset_curve segment section from lines [liStart : liStart + 1] in
       lineLists.

    Same interface as parse_segment_spline() but with offset direction point
    and offset distance for the offset curve.

    Return:
    . result: True when valid segmentTuple, else False with None
    . segmentTuple:
      - segmentType: 'offset_curve'
      - directionPoint3D: scaled offset coordinates in plane (x, y, 0) for
        offset direction with respect to the segments
      - offsetDistance: scaled offset distance with respect to the segments
    """
    resultFalse = (False, None)
    lineNr = liStart + 1  # index starts at 0, nr starts at 1
    # Check segment type
    segmentType = lineLists[liStart][0]
    if segmentType != 'offset_curve':
        ui.messageBox('No offset_curve segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Read 2D offset direction point and offset distance, in offset plane, from file line
    dataArr = lineLists[liStart + 1]
    result, offsetTuple = get_segment_offset(ui, title, filename, dataArr, scale)
    if not result:
        return resultFalse
    directionPoint3D, offsetDistance = offsetTuple
    segmentTuple = (segmentType, directionPoint3D, offsetDistance)
    return (True, segmentTuple)


def create_sketch_from_csv_file(ui, title, filename, hostComponent, verbosity=False):
    """Create sketch from CSV file, in hostComponent in Fusion360

    Input:
    . filename: full path and name of CSV file
    . hostComponent: place the sketch in hostComponent Sketches folder
    . verbosity: when False no print_text()
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    verbosity = False  # no print_text()

    # Parse CSV file
    result, sketchTuple = parse_csv_sketch_file(ui, title, filename)
    if not result:
        return
    planeNormal, planeOffset, segments = sketchTuple

    # Use stripped filename as offset plane name and as sketch name
    basename = os.path.basename(filename)
    basename = basename.split('.')[0]

    # Create sketch if there are valid segments
    if len(segments) > 0:
        # Create offset normal plane in hostComponent
        plane = schemacsv360.create_offset_normal_plane(hostComponent, basename, planeNormal, planeOffset)

        # Create sketch in offset plane
        sketch = utilities360.create_sketch_in_plane(hostComponent, basename, plane)
        interface360.print_text(ui, 'sketch x = ' + str(sketch.xDirection.asArray()), verbosity)
        interface360.print_text(ui, 'sketch y = ' + str(sketch.yDirection.asArray()), verbosity)

        # Keep list of segment curves for offset_curve
        curves = adsk.core.ObjectCollection.create()

        # Add segments into the sketch
        for segment in segments:
            segmentType = segment[0]
            if segmentType == 'spline':
                segmentPoints = segment[1]
                segmentTangents = segment[2]
                # Create spline
                spline = sketch.sketchCurves.sketchFittedSplines.add(segmentPoints)
                # Adjust tangents of spline
                adjust_spline_tangents(ui, planeNormal, spline, segmentTangents)
                curves.add(spline)
            elif segmentType == 'line':
                segmentPoints = segment[1]
                lines = sketch.sketchCurves.sketchLines
                # Create line pieces between subsequent points
                for pointIndex in range(0, segmentPoints.count - 1):
                    startPoint = segmentPoints.item(pointIndex)
                    endPoint = segmentPoints.item(pointIndex + 1)
                    if not startPoint.isEqualTo(endPoint):
                        # Create the line between the two different points
                        line = lines.addByTwoPoints(startPoint, endPoint)
                        curves.add(line)
            elif segmentType == 'offset_curve':
                directionPoint3D = segment[1]
                offsetDistance = segment[2]
                # curves = sketch.findConnectedCurves(spline)
                if curves.count > 0:
                    sketch.offset(curves, directionPoint3D, offsetDistance)
                    # Clear list for next offset_curve
                    curves.clear()
    else:
        ui.messageBox('No valid points in %s' % filename, title)


def create_sketches_from_csv_files(ui, title, folderName, hostComponent):
    """Create sketches from CSV files in folder, in hostComponent in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: place the sketch in hostComponent Sketches folder.
    Return: None

    Uses ui, title, folderName to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)
    if len(filenames) > 0:
        for filename in filenames:
            # Create sketch from CSV file in hostComponent
            interface360.print_text(ui, 'Create sketch for ' + filename)
            create_sketch_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No sketch CSV files in %s' % folderName, title)
