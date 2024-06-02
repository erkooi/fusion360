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
. first line: 'sketch' as filetype, name of the sketch, name of the group
  component for the sketch.
. second line: resolution 'mm' or 'cm'
. next line: 'offset_plane', plane normal axis 'x', 'y' or 'z', plane offset
  value.
  - normal 'x': yz-plane
  - normal 'y': zx-plane
  - normal 'z': xy-plane
. loop segments:
  - next line: segment type in validSegmentTypes
  - next lines dependent on segment type:
    . 'spline': list of two or more 2D point coordinates in sketch plane
      per 2D point x, y coordinates, optional spline handle angle in degrees
      and spline length.
    . 'line': list of two or more 2D point coordinates in sketch plane
      per 2D point x, y coordinates.
    . 'arc': list of one or more arcs defined by three 2D points x, y
      coordinates: start point, a point on the arc, end point in a counter
      clockwise direction.
    . 'circle': list of one or more circles, defined by center point (x, y)
      and radius.
    . 'ellipse': list of one or more ellipses, defined by center point (x, y),
      major axis point (mx, my) and a point (ex, ey) anywhere on the ellipse.
    . 'offset_curve': defines an offset curve for the previous segments, by
      direction point (x, y) for offset direction and offset distance.
    . 'point': list of two or more 2D point coordinates in sketch plane
      per 2D point x, y coordinates.
"""

import adsk.core
import math

import interfacefiles
import interface360
import utilities360
import schemacsv360


def read_segment_type(ui, title, filename, lineWord):
    """Read segment type from file line.

    Input:
    . lineWord: word from file line
    Return:
    . result: True when valid segmentType, else False with None
    . segmentType: string in validSegmentTypes
    """
    segmentType = lineWord
    if segmentType not in interfacefiles.validSegmentTypes:
        ui.messageBox('No valid segment type %s in %s' % (segmentType, filename), title)
        return (False, None)
    return (True, segmentType)


def get_segment_spline_point(ui, title, filename, planeNormal, unitScale, dataArr):
    """Get 2D spline point in offset plane with optional tangent angle and
    length.

    Map yz, zx, xy 2D point in dataArr to xy point in offset plane with z = 0.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . unitScale: scale factor between dataArr unit and API cm unit
    . dataArr: 2D point in offset plane
        [0] = x coordinate in offset plane
        [1] = y coordinate in offset plane
        Optional tangent at 2D spline point:
        [2] = angle in degrees of tangent handle at 2D spline point
        [3] = length of tangent handle at 2D spline point
    Return:
    . result: True when valid pointTuple, else False with None
    . pointTuple:
      - point3D: point (x, y, z) coordinates in plane with z = 0.
      - tangent: optional tangent (angle, length) of spline at point3D.

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    result, point3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                planeNormal, unitScale, dataArr)
    try:
        # Get point3D in offset plane
        if not result:
            raise Exception
        # Get optional point tangent angle and length
        angle = None
        if len(dataArr) > 2:
            angle = float(dataArr[2])
        length = None
        if len(dataArr) > 3:
            length = float(dataArr[3]) * unitScale
        if len(dataArr) > 4:
            raise Exception
        tangent = (angle, length)
        pointTuple = (point3D, tangent)
        result = (True, pointTuple)
    except Exception:
        ui.messageBox('No valid 2D spline point in %s of %s' % (dataArr, filename), title)
        result = (False, None)
    return result


def get_segment_offset(ui, title, filename, planeNormal, unitScale, dataArr):
    """Get offset parameters for offset_curve segment

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . unitScale: scale factor between dataArr unit and API cm unit
    . dataArr:
        [0] = x coordinate in plane, for offset direction of offset_curve
        [1] = y coordinate in plane, for offset direction of offset_curve
        [2] = offset distance
    Return:
    . result: True when valid offsetTuple, else False with None
    . offsetTuple:
      - directionPoint3D: scaled offset coordinates in plane (x, y, 0)
      - offsetDistance: scaled offset distance

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    try:
        # Get point3D for offset direction of offset_curve in offset plane
        result, directionPoint3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                             planeNormal, unitScale, dataArr)
        if not result:
            raise Exception
        # Get offset distance for offset_curve
        offsetDistance = float(dataArr[2]) * unitScale
        offsetTuple = (directionPoint3D, offsetDistance)
        result = (True, offsetTuple)
    except Exception:
        ui.messageBox('No valid offset_curve parameters in %s of %s' % (dataArr, filename), title)
        result = (False, None)
    return result


def get_segment_circle(ui, title, filename, planeNormal, unitScale, dataArr):
    """Get circle parameters for circle segment.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . unitScale: scale factor between dataArr unit and API cm unit
    . dataArr:
        [0] = center x coordinate in plane
        [1] = center y coordinate in plane
        [2] = radius
    Return:
    . result: True when valid circleTuple, else False with None
    . circleTuple:
      - centerPoint3D: center of circle coordinates in plane (x, y, 0)
      - radius: scaled radius of the circle

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    try:
        # Get point3D for center of circle in offset plane
        result, centerPoint3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                          planeNormal, unitScale, dataArr)
        if not result:
            raise Exception
        # Get radius of circle
        radius = float(dataArr[2]) * unitScale
        circleTuple = (centerPoint3D, radius)
        result = (True, circleTuple)
    except Exception:
        ui.messageBox('No valid circle parameters in %s of %s' % (dataArr, filename), title)
        result = (False, None)
    return result


def get_segment_ellipse(ui, title, filename, planeNormal, unitScale, dataArr):
    """Get ellipse parameters for ellipse segment.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . unitScale: scale factor between dataArr unit and API cm unit
    . dataArr:
        [0] = center x coordinate in plane
        [1] = center y coordinate in plane
        [2] = on major axis point x coordinate in plane
        [3] = on major axis point y coordinate in plane
        [4] = on ellipse point x coordinate in plane
        [5] = on ellipse point y coordinate in plane
    Return:
    . result: True when valid ellipseTuple, else False with None
    . ellipseTuple:
      - centerPoint3D: center of ellipse coordinates in plane (x, y, 0)
      - majorPoint3D: on major axis point of ellipse coordinates in plane
        (x, y, 0)
      - ellipsePoint3D: on ellipse point of ellipse coordinates in plane
        (x, y, 0)

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    try:
        # Get point3D points for ellipse in offset plane
        result1, centerPoint3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                           planeNormal, unitScale, dataArr[0:2])
        result2, majorPoint3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                          planeNormal, unitScale, dataArr[2:4])
        result3, ellipsePoint3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                            planeNormal, unitScale, dataArr[4:6])
        if not (result1 and result2 and result3):
            raise Exception
        ellipseTuple = (centerPoint3D, majorPoint3D, ellipsePoint3D)
        result = (True, ellipseTuple)
    except Exception:
        ui.messageBox('No valid ellipse parameters in %s of %s' % (dataArr, filename), title)
        result = (False, None)
    return result


def adjust_spline_tangents(ui, planeNormal, spline, segmentTangents):
    """Use segmentTangents to adjust the spline handles per spline point.

    The tangent in segmentTangents can adjust the angle, length of the handle
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


def find_sketch_segment_sections(ui, title, filename, lineLists):
    """Find sketch segment sections in lineLists.

    Input:
    . lineLists: list of lists of data values per read line
    Return:
    . result: True when valid sketchLocationsTuple, else False with None
    . sketchLocationsTuple:
      - sketchName: name of the sketch object
      - groupComponentName: group component for the sketch object
      - unitScale: scale factor between sketch unit and API cm unit
      - planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
      - planeOffset: offset from origin plane
      - segmentLocations: list of sketch segment sections in lineLists, with
        start line index, end line index and segmentType per section.

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    resultFalse = (False, None)
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            # Read file type
            if lineWord != 'sketch':
                return resultFalse
            sketchName = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
        elif li == 1:
            # Read units
            result, unitScale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        elif li == 2:
            if lineWord != 'offset_plane':
                return resultFalse
            # Read plane normal axis and offset of the sketch plane from lineArr
            result, planeTuple = schemacsv360.read_offset_plane(ui, title, filename, unitScale, lineArr[1:])
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
            if lineWord in interfacefiles.validSegmentTypes:
                # Append location and type of previous sketch segment
                if li > liStart + 1:
                    segmentLocations.append((liStart, liLast, segmentType))
                # Read new sketch segment type from file line
                result, segmentType = read_segment_type(ui, title, filename, lineWord)
                if not result:
                    return resultFalse
                liStart = li
            else:
                # Continue with current sketch segment
                liLast = li
    # Append location and type of last sketch segment
    segmentLocations.append((liStart, liLast, segmentType))
    # Successfully reached end of file
    sketchLocationsTuple = (sketchName, groupComponentName, unitScale, planeNormal, planeOffset, segmentLocations)
    return (True, sketchLocationsTuple)


def parse_sketch_segment_sections(ui, title, filename, planeNormal, unitScale, lineLists, segmentLocations):
    """Parse sketch segment sections in lineLists. The sketch segments sections
    are identified by a list of segmentLocations.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . unitScale: scale factor between sketch unit and API cm unit
    . lineLists: list of lists of data values per read line
    . segmentLocations: list of sketch segment sections in lineLists, with
      start line index, end line index and segmentType per section.
    Return:
    . result: True when valid segments, else False with None
    . segments: list of segmentTuple (segmentType, ... segment data ...)

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    resultFalse = (False, None)
    segments = []
    for (liStart, liLast, segmentType) in segmentLocations:
        result = False
        if segmentType == 'spline':
            result, segmentTuple = parse_segment_spline(ui, title, filename, planeNormal, unitScale,
                                                        liStart, liLast, lineLists)
        elif segmentType == 'line':
            result, segmentTuple = parse_segment_line(ui, title, filename, planeNormal, unitScale,
                                                      liStart, liLast, lineLists)
        elif segmentType == 'arc':
            result, segmentTuple = parse_segment_arc(ui, title, filename, planeNormal, unitScale,
                                                     liStart, liLast, lineLists)
        elif segmentType == 'offset_curve':
            result, segmentTuple = parse_segment_offset_curve(ui, title, filename, planeNormal, unitScale,
                                                              liStart, lineLists)
        elif segmentType == 'circle':
            result, segmentTuple = parse_segment_circle(ui, title, filename, planeNormal, unitScale,
                                                        liStart, liLast, lineLists)
        elif segmentType == 'ellipse':
            result, segmentTuple = parse_segment_ellipse(ui, title, filename, planeNormal, unitScale,
                                                         liStart, liLast, lineLists)
        elif segmentType == 'point':
            result, segmentTuple = parse_segment_point(ui, title, filename, planeNormal, unitScale,
                                                       liStart, liLast, lineLists)
        if result:
            segments.append(segmentTuple)
        else:
            return resultFalse
    # Successfully parsed all sketch segment sections in file
    return (True, segments)


def parse_csv_sketch_file(ui, title, filename):
    """Parse sketch CSV file.

    Reads offset plane and sketch segments from a sketch CSV file.

    Input:
    . filename: full path and name of a sketch CSV file
    Return:
    . result: True when valid sketchTuple, else False with None
    . sketchTuple:
      - sketchName: name of the sketch object
      - groupComponentName: group component for the sketch object
      - planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
      - planeOffset: offset from origin plane
      - segments: list of (segmentType, ... segment data ...)

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    resultFalse = (False, None)

    # Read sketch CSV file and remove comments and empty lines
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Find sketch segment sections in file lines
    result, sketchLocationsTuple = find_sketch_segment_sections(ui, title, filename, lineLists)
    if not result:
        return resultFalse
    sketchName, groupComponentName, unitScale, planeNormal, planeOffset, segmentLocations = sketchLocationsTuple

    # Parse sketch segment sections
    result, segments = parse_sketch_segment_sections(ui, title, filename,
                                                     planeNormal, unitScale, lineLists, segmentLocations)
    if not result:
        return resultFalse
    # Successfully reached end of file
    sketchTuple = (sketchName, groupComponentName, planeNormal, planeOffset, segments)
    return (True, sketchTuple)


def parse_segment_spline(ui, title, filename, planeNormal, unitScale, liStart, liLast, lineLists):
    """Parse spline segment section from file lines [liStart : liLast + 1] in
       lineLists.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . unitScale: scale factor between sketch unit and API cm unit
    . liStart: file line index of segmentType 'spline' in lineLists, so file
        line at liStart + 1 contains the point data for the first spline point
    . liEnd: file line at liEnd index contains point data for the last spline
        point
    . lineLists: list of file line data lists
    Return:
    . result: True when valid segmentTuple, else False with None
    . segmentTuple:
      - segmentType: 'spline'
      - segmentPoints: collection of point3D
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
        result, pointTuple = get_segment_spline_point(ui, title, filename, planeNormal, unitScale, dataArr)
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


def parse_segment_line(ui, title, filename, planeNormal, unitScale, liStart, liLast, lineLists):
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
        result, point3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                    planeNormal, unitScale, dataArr)
        if not result:
            return resultFalse
        segmentPoints.add(point3D)
    # Check segment length
    if segmentPoints.count < 2:
        ui.messageBox('Not enough points in segment in %s' % filename, title)
        return resultFalse
    segmentTuple = (segmentType, segmentPoints)
    return (True, segmentTuple)


def parse_segment_arc(ui, title, filename, planeNormal, unitScale, liStart, liLast, lineLists):
    """Parse arc segment section from lines [liStart : liLast + 1] in lineLists.

    Same interface as parse_segment_spline(), but with arc parameters.

    Return:
    . result: True when valid segmentTuple, else False with None
    . segmentTuple:
      - segmentType: 'arc'
      - point3D[]: three scaled point coordinates in plane (x, y, 0)
    """
    resultFalse = (False, None)
    lineNr = liStart + 1  # index starts at 0, nr starts at 1
    segmentArcs = []
    # Check segment type
    segmentType = lineLists[liStart][0]
    if segmentType != 'arc':
        ui.messageBox('No three point arc segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Read 2D points in offset plane, three 2D points per file line
    for li in range(liStart + 1, liLast + 1):
        dataArr = lineLists[li]
        if len(dataArr) != 6:
            ui.messageBox('No valid arc data in %s at %d' % (filename, lineNr), title)
            return resultFalse
        dataPoints = (dataArr[0:2], dataArr[2:4], dataArr[4:6])
        arcPoints = adsk.core.ObjectCollection.create()
        for dataPoint in dataPoints:
            result, point3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                        planeNormal, unitScale, dataPoint)
            if not result:
                ui.messageBox('No valid arc point3D in %s at %d' % (filename, lineNr), title)
                return resultFalse
            arcPoints.add(point3D)
        segmentArcs.append(arcPoints)
    segmentTuple = (segmentType, segmentArcs)
    return (True, segmentTuple)


def parse_segment_offset_curve(ui, title, filename, planeNormal, unitScale, liStart, lineLists):
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
    result, offsetTuple = get_segment_offset(ui, title, filename, planeNormal, unitScale, dataArr)
    if not result:
        return resultFalse
    directionPoint3D, offsetDistance = offsetTuple
    segmentTuple = (segmentType, directionPoint3D, offsetDistance)
    return (True, segmentTuple)


def parse_segment_circle(ui, title, filename, planeNormal, unitScale, liStart, liLast, lineLists):
    """Parse circle segment section from lines [liStart : liLast + 1] in
       lineLists.

    Same interface as parse_segment_spline(), but with circle parameters.

    Return:
    . result: True when valid segmentTuple, else False with None
    . segmentTuple:
      - segmentType: 'circle'
      - segmentCircles, list of circleTuples:
        . centerPoint3D: scaled circle center coordinates in plane (x, y, 0)
        . radius: scaled circle radius
    """
    resultFalse = (False, None)
    lineNr = liStart + 1  # index starts at 0, nr starts at 1
    segmentCircles = []
    # Check segment type
    segmentType = lineLists[liStart][0]
    if segmentType != 'circle':
        ui.messageBox('No circle segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Read 2D center point and radius, in offset plane, one circle per file line
    for li in range(liStart + 1, liLast + 1):
        dataArr = lineLists[li]
        result, circleTuple = get_segment_circle(ui, title, filename, planeNormal, unitScale, dataArr)
        if not result:
            return resultFalse
        segmentCircles.append(circleTuple)
    segmentTuple = (segmentType, segmentCircles)
    return (True, segmentTuple)


def parse_segment_ellipse(ui, title, filename, planeNormal, unitScale, liStart, liLast, lineLists):
    """Parse ellipse segment section from lines [liStart : liLast + 1] in
       lineLists.

    Same interface as parse_segment_spline(), but with ellipse parameters.

    Return:
    . result: True when valid segmentTuple, else False with None
    . segmentTuple:
      - segmentType: 'ellipse'
      - segmentEllipses, list of ellipseTuples:
        . centerPoint3D: scaled ellipse center coordinates in plane (x, y, 0)
        . majorPoint3D: scaled ellipse major axis point coordinates in plane
          (x, y, 0)
        . ellipsePoint3D: scaled ellipse point coordinates in plane (x, y, 0)
    """
    resultFalse = (False, None)
    lineNr = liStart + 1  # index starts at 0, nr starts at 1
    segmentEllipses = []
    # Check segment type
    segmentType = lineLists[liStart][0]
    if segmentType != 'ellipse':
        ui.messageBox('No ellipse segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Read 2D center, major and ellipse points, in offset plane, one ellipse per file line
    for li in range(liStart + 1, liLast + 1):
        dataArr = lineLists[li]
        result, ellipseTuple = get_segment_ellipse(ui, title, filename, planeNormal, unitScale, dataArr)
        if not result:
            return resultFalse
        segmentEllipses.append(ellipseTuple)
    segmentTuple = (segmentType, segmentEllipses)
    return (True, segmentTuple)


def parse_segment_point(ui, title, filename, planeNormal, unitScale, liStart, liLast, lineLists):
    """Parse point segment section from lines [liStart : liLast + 1] in
       lineLists.

    Same interface as parse_segment_spline(), but with point parameters.

    Return:
    . result: True when valid segmentTuple, else False with None
    . segmentTuple:
      - segmentType: 'point'
      - point3D: scaled point coordinates in plane (x, y, 0)
    """
    resultFalse = (False, None)
    lineNr = liStart + 1  # index starts at 0, nr starts at 1
    segmentPoints = adsk.core.ObjectCollection.create()
    # Check segment type
    segmentType = lineLists[liStart][0]
    if segmentType != 'point':
        ui.messageBox('No point segment in %s at %d' % (filename, lineNr), title)
        return resultFalse
    # Read 2D point, in offset plane, one point per file line
    for li in range(liStart + 1, liLast + 1):
        dataArr = lineLists[li]
        result, point3D = schemacsv360.get_3d_point_in_offset_plane(ui, title, filename,
                                                                    planeNormal, unitScale, dataArr)
        if not result:
            return resultFalse
        segmentPoints.add(point3D)
    segmentTuple = (segmentType, segmentPoints)
    return (True, segmentTuple)


def create_sketch_from_csv_file(ui, title, filename, hostComponent):
    """Create sketch from CSV file, in Fusion360

    Dependent on the groupComponentName the sketch will be put in the Sketches
    folder of hostComponent or hostComponent/groupComponent.

    Input:
    . filename: full path and name of CSV file
    . hostComponent: host component for the sketch
    Return: True CSV file is a valid sketch file, else False.

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    verbosity = False  # no print_text()

    # Parse CSV file
    result, sketchTuple = parse_csv_sketch_file(ui, title, filename)
    if not result:
        return False
    # Use sketch name also as object name for plane
    objectName, groupComponentName, planeNormal, planeOffset, segments = sketchTuple

    # Create sketch if there are valid segments
    if len(segments) > 0:
        # Create groupComponent in hostComponent for sketch object, if it does
        # not already exist, else use hostComponent if groupComponentName is
        # empty string or is the hostComponent.
        groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)

        # Create offset normal plane in groupComponent
        plane = schemacsv360.create_offset_normal_plane(groupComponent, objectName, planeNormal, planeOffset)

        # Create sketch in offset plane
        sketch = utilities360.create_sketch_in_plane(groupComponent, objectName, plane)
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
            elif segmentType == 'arc':
                segmentArcs = segment[1]
                arcs = sketch.sketchCurves.sketchArcs
                for segmentArc in segmentArcs:
                    # Create arc
                    startPoint3D = segmentArc.item(0)
                    curvePoint3D = segmentArc.item(1)
                    endPoint3D = segmentArc.item(2)
                    arc = arcs.addByThreePoints(startPoint3D, curvePoint3D, endPoint3D)
                    curves.add(arc)
            elif segmentType == 'circle':
                segmentCircles = segment[1]
                circles = sketch.sketchCurves.sketchCircles
                for segmentCircle in segmentCircles:
                    # Create circle
                    centerPoint3D = segmentCircle[0]
                    radius = segmentCircle[1]
                    circle = circles.addByCenterRadius(centerPoint3D, radius)
                    curves.add(circle)
            elif segmentType == 'ellipse':
                segmentEllipses = segment[1]
                ellipses = sketch.sketchCurves.sketchEllipses
                for segmentEllipse in segmentEllipses:
                    # Create ellipse
                    centerPoint3D = segmentEllipse[0]
                    majorPoint3D = segmentEllipse[1]
                    ellipsePoint3D = segmentEllipse[2]
                    ellipse = ellipses.add(centerPoint3D, majorPoint3D, ellipsePoint3D)
                    curves.add(ellipse)
            elif segmentType == 'offset_curve':
                directionPoint3D = segment[1]
                offsetDistance = segment[2]
                # curves = sketch.findConnectedCurves(spline)
                if curves.count > 0:
                    sketch.offset(curves, directionPoint3D, offsetDistance)
                    # Clear list for next offset_curve
                    curves.clear()
            elif segmentType == 'point':
                segmentPoints = segment[1]
                points = sketch.sketchPoints
                for point3D in segmentPoints:
                    # Create point
                    points.add(point3D)
    else:
        ui.messageBox('No valid sketch segments in %s' % filename, title)
        return False
    interface360.print_text(ui, 'Created sketch for ' + filename)
    return True


def create_sketches_from_csv_files(ui, title, folderName, hostComponent):
    """Create sketches from CSV files in folder, in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: host component for the sketches
    Return: None

    Uses ui, title, folderName to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)
    if len(filenames) > 0:
        for filename in filenames:
            # Create sketch from CSV file in hostComponent
            create_sketch_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No sketch CSV files in %s' % folderName, title)
