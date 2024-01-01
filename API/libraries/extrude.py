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
# Date: 27 dec 2023
"""Module to extrude a sketch profile defined in a csv file in Fusion360.

The profile is a sketch profile. One or more profiles can be extruded from the
same sketch. The profile index is 0 if there is only one profile. If there are
multiple sketch profiles, then manually find the index using the Fusion360 GUI.
The extrude result bodies keep the name of the participant bodies or get a
default name. With result_names the result bodies can be renamed.

Extrude CSV file format:
. comment lines or comment in line will be removed
. first line: 'extrude' as filetype
. second line: resolution 'mm' or 'cm'
. 3-th line: 'profile', sketch name, profile indices (default index 0, when
    no index is given)
. 4-th line: 'offset', offset value
. 5-th line: extent_type:
  - 'distance', distanceValues
  - 'to_object', toBodyName
. 6-th line: operation:
  - 'join', participantBodyNames
  - 'cut', participantBodyNames
  - 'intersect', participantBodyNames
  - 'new_body'
. 7-th line: 'result_names', resultBodyNames

  distanceValues:
  . one distance value for single side extent, or two distance values for both
    sides extent
  . the two distance values have same sign
  . first value is for positive direction
  . the distance values are relative to the profile offset

  participantBodyNames:
  . A participant body is ignored if it is missed by the extrusion
  . The original participant bodies are lost if they get modified
  . join:
    - extrude result gets name of first participantBodyNames
  . cut:
    - if cut only takes part of a participant body, then that body
      keeps its name.
    - if cut separates a participant body in parts, then the first part
      keeps the participant body name and any other part get the
      participant body name with (index).
  . intersect: similar as for cut

  resultBodyNames:
  . rename the extrude result bodies, the number of resultBodyNames must be
    equal to the number of extrude result bodies

Remark:
. No need to support: multiple profiles, extent from face, operation
  newcomponent.
"""

import adsk.fusion

import interfacefiles
import schemacsv360
import interface360
import utilities360

validExtrudeExtentType = ['distance', 'to_object']
validExtrudeOperations = ['join', 'cut', 'intersect', 'new_body']


def parse_csv_extrude_file(ui, title, filename):
    """Parse extrude CSV file.

    Reads extrude name and sketch name for profile from csv file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid ExtrudeTuple, else False with None
    . extrudeTuple:
      - profileTuple: sketch name, profile indices
      - offset: start extrude at offset distance from sketch plane
      - extentType: 'distance' or 'to_object'
      - toBodyName: body name for extent 'to_object'
      - distanceValues: extent extrude over distanceValues[0] from sketch plane
        offset, extent two sided if distanceValues[1] is given
      - operation: 'join', 'cut', 'intersect', 'new_body'
      - participantBodyNames: body name(s) for join, cut or intersect operation
      - resultBodyNames: rename result body or bodies

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for extrude
    resultFalse = (False, None)
    profileIndices = [0]  # default use profile 0
    offset = 0
    distanceValues = []
    toBodyName = ''
    participantBodyNames = []
    resultBodyNames = ''
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'extrude':
                return resultFalse
        elif li == 1:
            # Read units
            result, scale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        elif li == 2:
            if lineWord == 'profile':
                sketchName = lineArr[1]
                if len(lineArr) > 2:
                    profileIndices = interfacefiles.convert_entries_to_integers(lineArr[2:])
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        elif li == 3:
            if lineWord == 'offset':
                offset = float(lineArr[1]) * scale
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        elif li == 4:
            result, extentTuple = _parse_extentType(ui, li, lineArr, scale)
            if result:
                extentType, distanceValues, toBodyName = extentTuple
            else:
                return resultFalse
        elif li == 5:
            result, operationTuple = _parse_operation(ui, li, lineArr)
            if result:
                operation, participantBodyNames = operationTuple
            else:
                return resultFalse
        elif li == 6:
            if lineWord == 'result_names':
                if len(lineArr) > 1:
                    resultBodyNames = lineArr[1:]
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        else:
            return resultFalse

    # Successfully reached end of file
    profileTuple = (sketchName, profileIndices)
    extentTuple = (offset, extentType, distanceValues, toBodyName)
    operationTuple = (operation, participantBodyNames, resultBodyNames)
    extrudeTuple = (profileTuple, extentTuple, operationTuple)
    return (True, extrudeTuple)


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


def _parse_extentType(ui, lineIndex, lineArr, scale):
    """Parse lineArr for extentType with distance or toBodyName."""
    resultFalse = (False, None)
    if lineArr[0] == 'extent_type':
        extentType = lineArr[1]
        distanceValues = []
        toBodyName = ''
        if extentType == 'distance':
            distanceValues.append(float(lineArr[2]) * scale)  # one side
            if len(lineArr) > 3:
                distanceValues.append(float(lineArr[3]) * scale)  # two sided
        elif extentType == 'to_object':
            toBodyName = lineArr[2]
        else:
            interface360.error_text(ui, 'Unknown extent_type ' + extentType)
            return resultFalse
    else:
        interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineArr[0], lineIndex))
        return resultFalse
    return (True, (extentType, distanceValues, toBodyName))


def extrude_profiles(profileTuple, operationTuple, extentTuple):
    """Extrude the profile(s).

    Input:
    . profileTuple: sketch with list of profiles to extrude
    . operationTuple: extrude operation parameters
    . extentTuple: extrude extent parameters
    Return:
    . extrudeResult : extrudeFeature object with result of the extrude
    """
    # Extract tuples
    sketch, profiles = profileTuple
    operation, participantBodies, resultBodyNames = operationTuple
    offset, extentType, distanceValues, toBody = extentTuple

    # Create extrude feature input
    # . The extrudeFeatures has to be obtained from the same component that
    #   contains the sketches, therefore use sketch.parentComponent instead of
    #   hostComponent.
    operationEnum = utilities360.get_feature_operation_enum(operation)
    extrudeFeatures = sketch.parentComponent.features.extrudeFeatures
    extrudeFeatureInput = extrudeFeatures.createInput(profiles, operationEnum)

    # Select extent type
    if extentType == 'distance':
        # Create a distance extent definition
        distanceValueInputOne = adsk.core.ValueInput.createByReal(distanceValues[0])
        distanceExtentOne = adsk.fusion.DistanceExtentDefinition.create(distanceValueInputOne)
        if len(distanceValues) == 1:
            # One side extent distance
            extrudeFeatureInput.setOneSideExtent(distanceExtentOne,
                                                 adsk.fusion.ExtentDirections.PositiveExtentDirection)
        else:
            # Two sides extent distance, positive direction is second argument
            # in setTwoSidesExtent()
            distanceValueInputTwo = adsk.core.ValueInput.createByReal(distanceValues[1])
            distanceExtentTwo = adsk.fusion.DistanceExtentDefinition.create(distanceValueInputTwo)
            extrudeFeatureInput.setTwoSidesExtent(distanceExtentTwo, distanceExtentOne)
    else:  # 'to_object'
        # Create a to-entity extent definition
        isChained = True
        toEntityExtent = adsk.fusion.ToEntityExtentDefinition.create(toBody, isChained)
        # Set the one side extent with the to-entity-extent-definition, and with a taper angle of 0 degree
        extrudeFeatureInput.setOneSideExtent(toEntityExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

    # Include any participantBodies in extrude
    if participantBodies:
        extrudeFeatureInput.participantBodies = participantBodies

    # Set extent start offset
    if offset:
        # Create an offset type start definition
        offsetValueInput = adsk.core.ValueInput.createByReal(offset)
        offsetStart = adsk.fusion.OffsetStartDefinition.create(offsetValueInput)
        # Set the start extent of the extrusion
        extrudeFeatureInput.startExtent = offsetStart

    # Create the extrusion
    extrudeResult = extrudeFeatures.add(extrudeFeatureInput)
    return extrudeResult


def extrude_from_csv_file(ui, title, filename, hostComponent):
    """Extrude from CSV file, in hostComponent Bodies folder in Fusion360

    Input:
    . filename: full path and name of CSV file
    . hostComponent: look for sketch profile anywhere in hostComponent folder.
    Return:
    . True when extrude was done, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, extrudeTuple = parse_csv_extrude_file(ui, title, filename)
    if not result:
        return False
    # Extract tuples
    profileTuple, extentTuple, operationTuple = extrudeTuple
    sketchName, profileIndices = profileTuple
    offset, extentType, distanceVales, toBodyName = extentTuple
    operation, participantBodyNames, resultBodyNames = operationTuple

    interface360.print_text(ui, 'sketchName ' + profileTuple[0])
    interface360.print_text(ui, 'profileIndices ' + str(profileTuple[1]))
    interface360.print_text(ui, 'extentType ' + extentType)
    interface360.print_text(ui, 'distanceVales ' + str(distanceVales))
    interface360.print_text(ui, 'toBodyName ' + toBodyName)
    interface360.print_text(ui, 'operation ' + operation)
    interface360.print_text(ui, 'resultBodyNames ' + str(resultBodyNames))

    # Find profile(s) in sketch and update profileTuple
    sketch = utilities360.find_sketch_anywhere(hostComponent, sketchName)
    if not sketch:
        interface360.error_text(ui, 'Sketch %s not found' % sketchName)
        return False
    profiles = utilities360.find_profiles_collection(ui, sketch, profileIndices)
    if not profiles:
        return False
    profileTuple = (sketch, profiles)

    # Find participant bodies in hostComponent and update operationTuple
    participantBodies = []
    if operation in ['join', 'cut', 'intersect']:
        for bodyName in participantBodyNames:
            body = utilities360.find_body_anywhere(hostComponent, bodyName)
            if not body:
                interface360.error_text(ui, 'Participant body %s not found' % bodyName)
                return False
            participantBodies.append(body)
    operationTuple = (operation, participantBodies, resultBodyNames)

    # Find to_object body and update extentTuple
    toBody = None
    if toBodyName:
        toBody = utilities360.find_body_anywhere(hostComponent, toBodyName)
        if not body:
            interface360.error_text(ui, 'To object body %s not found' % toBodyName)
            return False
    extentTuple = (offset, extentType, distanceVales, toBody)

    # Perform the extrusion
    extrudeResult = extrude_profiles(profileTuple, operationTuple, extentTuple)

    # Rename the body or bodies of the extrusion
    if operation == 'new_body':
        newBody = extrudeResult.bodies.item(0)
        newBody.name = resultBodyNames[0]
    elif operation in ['join', 'cut', 'intersect']:
        nofResultBodyNames = len(resultBodyNames)
        if nofResultBodyNames > 0:
            if len(resultBodyNames) == extrudeResult.bodies.count:
                for bi in range(extrudeResult.bodies.count):
                    body = extrudeResult.bodies.item(bi)
                    body.name = resultBodyNames[bi]
            else:
                interface360.print_text(ui, 'Number of result_names %d != %d result bodies.count' %
                                        (nofResultBodyNames, extrudeResult.bodies.count))
                return False
    interface360.print_text(ui, 'Extruded for ' + filename)
    return True


def extrudes_from_csv_files(ui, title, folderName, hostComponent):
    """Extrudes from CSV files in folder, in hostComponent in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: look for sketch profile anywhere in hostComponent folder.
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Extrude from CSV file in hostComponent
            extrude_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No extrude CSV files in %s' % folderName, title)
