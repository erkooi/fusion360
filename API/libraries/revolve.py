################################################################################
# Copyright 2024 E. Kooistra
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
# Date: 5 oct 2024
"""Module to revolve a sketch profile defined in a csv file in Fusion360.

The sketch profile index is 0 if there is only one profile. If the sketch
contains multiple profiles, then manually find the indices using the Fusion360
GUI. The revolve result bodies keep the name of the participant bodies or get a
default name. With revolve_results the result bodies can be renamed.

Revolve CSV file format:
. comment lines or comment in line will be removed
. first line: 'revolve' as filetype, name of the revolve file, name of the
  group component for the revolve results.
. second line: resolution 'mm' or 'cm'
. 3-rd line:
  - 'profile', sketch name, profile indices,
    Default index 0, when no index is given. The profiles must be coplanar,
    which is typically the case since they are in the same sketch.
. 4-th line:
  - 'rotation_line': sketch name, line index
  - 'rotation_axis': axis name 'x', 'y', or 'z'
    The axis must be in the same plane as the profiles, or it will be
    projected in that plane.
. 5-th line:
  - 'rotation_angles', rotation angles for one side or two sides extent
. 6-th line: operation:
  - 'join', participantBodyNames
  - 'cut', participantBodyNames
  - 'intersect', participantBodyNames
  - 'new_body'
. Optional lines:
  - 'revolve_results', resultBodyNames
  - 'light_bulb', 'on' or 'off' of result bodies (default is 'on')

  rotationAngles:
  . one angle value for single side extent, or two angle values for both
    sides extent
  . the two angle values have same sign
  . first angle value is for positive direction
  . the angle values are relative to the profile plane

  participantBodyNames:
  . A participant body is ignored if it is missed by the revolve
  . The original participant bodies are lost if they get modified
  . join:
    - revolve result gets name of first participantBodyNames
  . cut:
    - if cut only takes part of a participant body, then that body
      keeps its name.
    - if cut separates a participant body in parts, then the first part
      keeps the participant body name and any other part get the
      participant body name with (index).
  . intersect: similar as for cut

  resultBodyNames:
  . If resultBodyNames is not specified, then keep the default names, else
    rename the revolve result bodies, the number of resultBodyNames must be
    equal to the number of revolve result bodies.
"""

import math
import adsk.fusion

import interfacefiles
import schemacsv360
import interface360
import utilities360


def parse_csv_revolve_file(ui, title, filename):  # noqa: C901 (ignore function is too complex)
    """Parse revolve CSV file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid revolveTuple, else False with None
    . revolveTuple:
      - locationtuple:
        . revolveFilename: name of revolve CSV file, not used
        . groupComponentName: group component for the revolve result
      - sketchTuple:
        . profileSketchName: name of sketch, for profile to revolve
        . profileIndices: profile indices
      - rotationTuple:
        . rotationAxisName: 'x', 'y', or 'z' when used, else ''
        . rotationLineSketchName: name of sketch with rotation line when used,
          else ''
        . rotationLineIndex: lineIndex of rotation line
        . rotationAngles: revolve one sided over rotationAngles[0], or two
          sided if rotationAngles[1] is also given
      - operationTuple:
        . operation: 'join', 'cut', 'intersect', 'new_body'
        . participantBodyNames: body name(s) for join, cut or intersect
          operation
        . resultBodyNames: optional rename result body or bodies
        . lightBulbOn: optional control for light bulb of result bodies

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for revolve
    resultFalse = (False, None)
    profileSketchName = ''
    profileIndices = [0]  # default use index 0 for sketch profile
    rotationAxisName = ''
    rotationLineSketchName = ''
    rotationLineIndex = 0  # default use index 0 for sketch line
    rotationAngles = []
    participantBodyNames = []
    resultBodyNames = ''
    lightBulbOn = True
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'revolve':
                return resultFalse
            revolveFilename = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
        elif li == 1:
            result, scale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        elif li == 2:
            if lineWord == 'profile':
                profileSketchName = lineArr[1]
                if len(lineArr) > 2:
                    profileIndices = interfacefiles.convert_entries_to_integers(lineArr[2:])
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        elif li == 3:
            if lineWord in ['rotation_axis', 'rotation_line']:
                if lineWord == 'rotation_axis':
                    rotationAxisName = lineArr[1]
                    if rotationAxisName not in interfacefiles.validPlaneNormals:
                        interface360.error_text(ui, 'Unexpected rotation axis %s at li = %d' % (rotationAxisName, li))
                        return resultFalse
                elif lineWord == 'rotation_line':
                    rotationLineSketchName = lineArr[1]
                    if len(lineArr) > 2:
                        rotationLineIndex = int(lineArr[2])
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        elif li == 4:
            if lineWord == 'rotation_angles':
                rotationAngles.append(math.radians(float(lineArr[1])))  # one side
                if len(lineArr) > 2:
                    rotationAngles.append(math.radians(float(lineArr[2])))  # two sided
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        elif li == 5:
            result, operationTuple = _parse_operation(ui, li, lineArr)
            if result:
                operation, participantBodyNames = operationTuple
            else:
                return resultFalse
        else:
            if lineWord == 'revolve_results':
                if len(lineArr) > 1:
                    resultBodyNames = lineArr[1:]
            elif lineWord == 'light_bulb':
                lightBulbOn = True if lineArr[1] == 'on' else False
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse

    # Successfully reached end of file
    locationTuple = (revolveFilename, groupComponentName)
    sketchTuple = (profileSketchName, profileIndices)
    rotationTuple = (rotationAxisName, rotationLineSketchName, rotationLineIndex, rotationAngles)
    operationTuple = (operation, participantBodyNames, resultBodyNames, lightBulbOn)
    revolveTuple = (locationTuple, sketchTuple, rotationTuple, operationTuple)
    return (True, revolveTuple)


def _parse_operation(ui, lineIndex, lineArr):
    """Parse lineArr for operation and participantBodyNames."""
    resultFalse = (False, None)
    if lineArr[0] == 'operation':
        operation = lineArr[1]
        participantBodyNames = []
        if operation in ['join', 'cut', 'intersect']:
            participantBodyNames = lineArr[2:]
        return (True, (operation, participantBodyNames))
    else:
        interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineArr[0], lineIndex))
        return resultFalse


def revolve_profiles(ui, hostComponent, sketchTuple, rotationTuple, operationTuple):
    """Revolve the profile(s) from sketchTuple.

    Input:
    . hostComponent: Use hostComponent for construction axis
    . sketchTuple: sketch object with profiles to revolve
    . operationTuple: revolve operation parameters
    . rotationTuple: revolve extent parameters
    Return:
    . revolveResult : revolveFeature object with result of the revolve

    Uses ui to report faults via Fusion360 GUI.
    """
    verbosity = False

    # Extract tuples
    sketch, profiles = sketchTuple
    operation, participantBodies, resultBodyNames, lightBulbOn = operationTuple
    rotationAxisName, rotationLineSketchName, rotationLineIndex, rotationAngles = rotationTuple

    # Create revolve feature input
    # . Assume the revolveFeatures has to be obtained from the same component
    #   that contains the sketch, therefore use sketch.parentComponent instead
    #   of hostComponent.
    operationEnum = schemacsv360.get_feature_operation_enum(operation)
    axisLine = utilities360.get_axis_line(ui, hostComponent,
                                          rotationAxisName, rotationLineSketchName, rotationLineIndex)
    revolveFeatures = sketch.parentComponent.features.revolveFeatures
    revolveFeatureInput = revolveFeatures.createInput(profiles, axisLine, operationEnum)
    creationOccurrence = revolveFeatureInput.creationOccurrence
    if creationOccurrence:
        interface360.print_text(ui, 'revolveFeatureInput.creationOccurrence.name ' + creationOccurrence.name, verbosity)

    # Create an angle extent definition
    angleValueInputOne = adsk.core.ValueInput.createByReal(rotationAngles[0])
    if len(rotationAngles) == 1:
        # One side extent angle
        isSymmetric = False
        revolveFeatureInput.setAngleExtent(isSymmetric, angleValueInputOne)
    else:
        # Two sides extent angle, positive direction is second argument
        # in setTwoSidesExtent()
        angleValueInputTwo = adsk.core.ValueInput.createByReal(rotationAngles[1])
        revolveFeatureInput.setTwoSideAngleExtent(angleValueInputOne, angleValueInputTwo)

    # Include any participantBodies in revolve
    if participantBodies:
        revolveFeatureInput.participantBodies = participantBodies

    # Perform the revolve
    revolveResult = revolveFeatures.add(revolveFeatureInput)

    # Control light bulb of result bodies
    for bi in range(revolveResult.bodies.count):
        body = revolveResult.bodies.item(bi)
        body.isLightBulbOn = lightBulbOn

    # TODO (for extrude, may also apply for revolve):
    # Find out why join = 0 yields same as new_body = 3, while intersect = 2
    # and cut = 1 yield expected result
    # interface360.error_text(ui, 'operation = ' + str(revolveFeatureInput.operation))
    return revolveResult


def revolve_from_csv_file(ui, title, filename, hostComponent):
    """Revolve from CSV file, in hostComponent Bodies folder in Fusion360

    Input:
    . filename: full path and name of CSV file
    . hostComponent: look for sketch profile anywhere in hostComponent folder.
    Return:
    . True when revolve was done, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, revolveTuple = parse_csv_revolve_file(ui, title, filename)
    if not result:
        return False
    # Extract tuples, revolveFilename is not used
    locationTuple, sketchTuple, rotationTuple, operationTuple = revolveTuple
    _, groupComponentName = locationTuple
    profileSketchName, profileIndices = sketchTuple
    operation, participantBodyNames, resultBodyNames, lightBulbOn = operationTuple

    # Create groupComponent in hostComponent for revolved bodies objects, if
    # it does not already exist, else use hostComponent if groupComponentName
    # is empty string or is the hostComponent.
    groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)

    # Find sketch profile to revolve anywhere in hostComponent
    sketchTuple = utilities360.find_sketch_and_profiles(ui, hostComponent, profileSketchName, profileIndices)

    # Find participant bodies in hostComponent and update operationTuple
    participantBodies = utilities360.find_participant_bodies(ui, hostComponent, participantBodyNames, operation)
    operationTuple = (operation, participantBodies, resultBodyNames, lightBulbOn)

    # Perform the revolve feature
    revolveResult = revolve_profiles(ui, hostComponent, sketchTuple, rotationTuple, operationTuple)

    # Rename the body or bodies of the revolve
    result, resultBodies = _rename_result_bodies(ui, resultBodyNames, revolveResult)
    if not result:
        interface360.error_text(ui, 'Rename result revolve bodies with %s failed' % str(resultBodyNames))
        return False

    # Move revolved bodies to the groupComponent, if the groupComponent is
    # another component then the parentComponent of the sketch.
    # . Use groupComponent in hostComponent for revolved bodies objects
    # . Get parentComponent of the sketch, because that is where the
    #   resultBodies are. No need for the profiles here.
    sketch, _ = sketchTuple
    if groupComponent != sketch.parentComponent:
        groupOccurrence = utilities360.get_occurrence_anywhere(groupComponent)
        for body in resultBodies:
            utilities360.move_body_to_occurrence(body, groupOccurrence)

    interface360.print_text(ui, 'Revolved for ' + filename)
    return True


def _rename_result_bodies(ui, resultBodyNames, revolveResult):
    """Rename bodies in revolveResult with names from resultBodyNames

    Input:
    . resultBodyNames: if list is empty, then keep default names, else use
      names from list to rename the bodies in revolveResult. If resultBodyNames
      contains not the same amount of names as the number of bodies in
      revolveResult, then report error via ui.
    . revolveResult: result feature of revolve

    Return:
    . result: True when rename went OK, else False
    . resultBodies: list of revolve result body objects

    Uses ui to report faults via Fusion360 GUI.
    """
    resultFalse = (False, None)
    resultBodies = []
    nofResultBodyNames = len(resultBodyNames)
    if nofResultBodyNames > 0:
        if len(resultBodyNames) == revolveResult.bodies.count:
            # Rename the body or bodies of the revolve
            for bi in range(revolveResult.bodies.count):
                body = revolveResult.bodies.item(bi)
                body.name = resultBodyNames[bi]
                resultBodies.append(body)
            return (True, resultBodies)
        else:
            # Report actual revolve body names
            interface360.error_text(ui, 'revolve resultBodyNames = ' + str(resultBodyNames))
            interface360.error_text(ui, 'revolve nofResultBodyNames %d != %d revolveResult.bodies.count' %
                                    (nofResultBodyNames, revolveResult.bodies.count))
            for bi in range(revolveResult.bodies.count):
                body = revolveResult.bodies.item(bi)
                interface360.error_text(ui, 'revolve body.name = ' + str(body.name))
            return resultFalse
    else:
        # Keep default body names of the revolve
        for bi in range(revolveResult.bodies.count):
            body = revolveResult.bodies.item(bi)
            resultBodies.append(body)
        return (True, resultBodies)


def revolves_from_csv_files(ui, title, folderName, hostComponent):
    """Revolves from CSV files in folder, in hostComponent in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: look for sketch profile anywhere in hostComponent folder.
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Revolve from CSV file in hostComponent
            revolve_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No revolve CSV files in %s' % folderName, title)
