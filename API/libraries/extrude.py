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
"""Module to extrude a planar defined in a csv file in Fusion360.

The planar is a sketch profile or a body face. One or more planars can be
extruded from the same sketch or body. The planar index is 0 if there is only
one profile or face. If there are multiple planars, then manually find the
index using the Fusion360 GUI.
The extrude result bodies keep the name of the participant bodies or get a
default name. With extrude_results the result bodies can be renamed.

Extrude CSV file format:
. comment lines or comment in line will be removed
. first line: 'extrude' as filetype, name of the extrude file, name of the
  group component for the extrude results.
. second line: resolution 'mm' or 'cm'
. 3-rd line:
  - 'profile', sketch name, profile indices, or
  - 'face', body name, face indices,
    default index 0, when no index is given. The profiles or faces must be
    coplanar.
. 4-th line: 'offset', offset value
. 5-th line: 'taper_angle', taper angle value in degrees for one side or two
    sided extent
. 6-th line: extent_type:
  - 'distance', distanceValues for one side or two sides extent
  - 'to_object', toBodyName
. 7-th line: operation:
  - 'join', participantBodyNames
  - 'cut', participantBodyNames
  - 'intersect', participantBodyNames
  - 'new_body'
. 8-th line: 'extrude_results', resultBodyNames

  distanceValues:
  . one distance value for single side extent, or two distance values for both
    sides extent
  . the two distance values have same sign
  . first value is for positive direction
  . the distance values are relative to the planer (profile or face) offset

  participantBodyNames:
  . A participant body is ignored if it is missed by the extrude
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
  . If resultBodyNames is not specified, then keep the default names, else
    rename the extrude result bodies, the number of resultBodyNames must be
    equal to the number of extrude result bodies.
"""

import math
import adsk.fusion

import interfacefiles
import schemacsv360
import interface360
import utilities360

validExtrudeExtentType = ['distance', 'to_object']
validExtrudeOperations = ['join', 'cut', 'intersect', 'new_body']


def parse_csv_extrude_file(ui, title, filename):  # noqa: C901 (ignore function is too complex)
    """Parse extrude CSV file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid ExtrudeTuple, else False with None
    . extrudeTuple:
      - locationtuple:
        . extrudeFilename: name of extrude CSV file, not used
        . groupComponentName: group component for the extrude result
      - planarTuple:
        . sketch name: name of sketch, for profile to extrude
        . from body name: name of body, for face to extrude
        . planar (profile or face) indices
      - extentTuple:
        . offset: start extrude at offset distance from sketch plane or body
          face
        . taperAngles: taper angle in degrees for the extrude, one or two
          values for one side or two sided extent extrude
        . extentType: 'distance' or 'to_object'
        . distanceValues: extent extrude over distanceValues[0] from planar
          offset, extent two sided if distanceValues[1] is given
        . toBodyName: body name for extent 'to_object'
      - operationTuple:
        . operation: 'join', 'cut', 'intersect', 'new_body'
        . participantBodyNames: body name(s) for join, cut or intersect
          operation
        . resultBodyNames: optional rename result body or bodies

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for extrude
    resultFalse = (False, None)
    profileSketchName = ''
    textSketchName = ''
    fromBodyName = ''
    planarIndices = [0]  # default use index 0 for sketch profile or body face
    offset = 0
    taperAngles = []
    distanceValues = []
    toBodyName = ''
    participantBodyNames = []
    resultBodyNames = ''
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'extrude':
                return resultFalse
            extrudeFilename = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
        elif li == 1:
            result, scale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        elif li == 2:
            if lineWord in ['profile', 'text', 'face']:
                if lineWord == 'profile':
                    profileSketchName = lineArr[1]
                elif lineWord == 'text':
                    textSketchName = lineArr[1]
                elif lineWord == 'face':
                    fromBodyName = lineArr[1]
                if len(lineArr) > 2:
                    planarIndices = interfacefiles.convert_entries_to_integers(lineArr[2:])
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
            if lineWord == 'taper_angle':
                taperAngles.append(math.radians(float(lineArr[1])))  # one side
                if len(lineArr) > 2:
                    taperAngles[1] = math.radians(float(lineArr[2]))  # two sided
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        elif li == 5:
            result, extentTuple = _parse_extent_type(ui, li, lineArr, scale)
            if result:
                extentType, distanceValues, toBodyName = extentTuple
                if len(distanceValues) == 2 and len(taperAngles) == 1:
                    taperAngles.append(0)  # default use no taper on second side
            else:
                return resultFalse
        elif li == 6:
            result, operationTuple = _parse_operation(ui, li, lineArr)
            if result:
                operation, participantBodyNames = operationTuple
            else:
                return resultFalse
        elif li == 7:
            if lineWord == 'extrude_results':
                if len(lineArr) > 1:
                    resultBodyNames = lineArr[1:]
            else:
                interface360.error_text(ui, 'Unexpected key word %s at li = %d' % (lineWord, li))
                return resultFalse
        else:
            return resultFalse

    # Successfully reached end of file
    locationTuple = (extrudeFilename, groupComponentName)
    planarTuple = (profileSketchName, textSketchName, fromBodyName, planarIndices)
    extentTuple = (offset, taperAngles, extentType, distanceValues, toBodyName)
    operationTuple = (operation, participantBodyNames, resultBodyNames)
    extrudeTuple = (locationTuple, planarTuple, extentTuple, operationTuple)
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


def _parse_extent_type(ui, lineIndex, lineArr, scale):
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


def extrude_planars(ui, objectTuple, operationTuple, extentTuple):
    """Extrude the planar(s) from objectTuple.

    Input:
    . objectTuple: sketch object with profiles or body object with faces to
      extrude
    . operationTuple: extrude operation parameters
    . extentTuple: extrude extent parameters
    Return:
    . extrudeResult : extrudeFeature object with result of the extrude

    Uses ui to report faults via Fusion360 GUI.
    """
    verbosity = False

    # Extract tuples
    object, planars = objectTuple
    operation, participantBodies, resultBodyNames = operationTuple
    offset, taperAngles, extentType, distanceValues, toBody = extentTuple
    copiedToBody = None

    # Create extrude feature input
    # . The extrudeFeatures has to be obtained from the same component that
    #   contains the object, therefore use object.parentComponent instead of
    #   hostComponent.
    operationEnum = schemacsv360.get_feature_operation_enum(operation)
    extrudeFeatures = object.parentComponent.features.extrudeFeatures
    extrudeFeatureInput = extrudeFeatures.createInput(planars, operationEnum)
    creationOccurrence = extrudeFeatureInput.creationOccurrence
    if creationOccurrence:
        interface360.print_text(ui, 'extrudeFeatureInput.creationOccurrence.name ' + creationOccurrence.name, verbosity)

    # Select extent type
    taperAngleInputOne = adsk.core.ValueInput.createByReal(taperAngles[0])
    if extentType == 'distance':
        # Create a distance extent definition
        distanceValueInputOne = adsk.core.ValueInput.createByReal(distanceValues[0])
        distanceExtentOne = adsk.fusion.DistanceExtentDefinition.create(distanceValueInputOne)
        if len(distanceValues) == 1:
            # One side extent distance
            extrudeFeatureInput.setOneSideExtent(distanceExtentOne,
                                                 adsk.fusion.ExtentDirections.PositiveExtentDirection,
                                                 taperAngleInputOne)
        else:
            # Two sides extent distance, positive direction is second argument
            # in setTwoSidesExtent()
            distanceValueInputTwo = adsk.core.ValueInput.createByReal(distanceValues[1])
            distanceExtentTwo = adsk.fusion.DistanceExtentDefinition.create(distanceValueInputTwo)
            taperAngleInputTwo = adsk.core.ValueInput.createByReal(taperAngles[1])
            extrudeFeatureInput.setTwoSidesExtent(distanceExtentTwo, distanceExtentOne,
                                                  taperAngleInputTwo, taperAngleInputOne)
    else:  # 'to_object'
        # Create a to-entity extent definition
        interface360.print_text(ui, 'object.parentComponent.name ' + object.parentComponent.name, verbosity)
        interface360.print_text(ui, 'toBody.parentComponent.name ' + toBody.parentComponent.name, verbosity)
        interface360.print_text(ui, 'object.name ' + object.name, verbosity)
        interface360.print_text(ui, 'toBody.name ' + toBody.name, verbosity)
        # TODO:
        # If the object and toBody are not in the same component, and the
        # object is not in the upstream component of the toBody (i.e. the
        # hostComponent), then the extrudeFeatureInput with
        # toEntityExtentDefinition is not accepted by extrudeFeatures.add().
        # I do not know how to use extrudeFeatureInput.creationOccurrence to
        # handle this, because all these parentOccurrence settings fail:
        # . parentOccurrence = utilities360.get_root_component(object.parentComponent)
        # . parentOccurrence = utilities360.get_occurrence_anywhere(object.parentComponent)
        # . parentOccurrence = utilities360.get_occurrence_anywhere(toBody.parentComponent)
        # . parentOccurrence = utilities360.get_occurrence_anywhere(toBody.parentComponent.parentDesign.activeComponent)
        #   extrudeFeatureInput.creationOccurrence = parentOccurrence
        # Workaround:
        # Copy the toBody to the object.parentComponent, do the extrude and
        # then remove the copied toBody
        isChained = True
        if toBody.parentComponent == object.parentComponent:
            # Use the toBody
            toEntityExtentDefinition = adsk.fusion.ToEntityExtentDefinition.create(toBody, isChained)
        else:
            # Use a copy of the toBody
            parentOccurrence = utilities360.get_occurrence_anywhere(object.parentComponent)
            copiedToBody = utilities360.copy_body_to_occurrence(toBody, parentOccurrence)
            toEntityExtentDefinition = adsk.fusion.ToEntityExtentDefinition.create(copiedToBody, isChained)

        # Set the one side extent with the to-entity-extent-definition, and with a taper angle
        extrudeFeatureInput.setOneSideExtent(toEntityExtentDefinition,
                                             adsk.fusion.ExtentDirections.PositiveExtentDirection,
                                             taperAngleInputOne)

    # Include any participantBodies in extrude
    if participantBodies:
        extrudeFeatureInput.participantBodies = participantBodies

    # Set extent start offset
    if offset:
        # Create an offset type start definition
        offsetValueInput = adsk.core.ValueInput.createByReal(offset)
        offsetStart = adsk.fusion.OffsetStartDefinition.create(offsetValueInput)
        # Set the start extent of the extrude
        extrudeFeatureInput.startExtent = offsetStart

    # Perform the extrude
    extrudeResult = extrudeFeatures.add(extrudeFeatureInput)

    # Remove the copiedToBody
    if copiedToBody:
        utilities360.remove_body(copiedToBody)

    # TODO:
    # Find out why join = 0 yields same as new_body = 3, while intersect = 2
    # and cut = 1 yield expected result
    # interface360.error_text(ui, 'operation = ' + str(extrudeFeatureInput.operation))
    return extrudeResult


def extrude_from_csv_file(ui, title, filename, hostComponent):
    """Extrude from CSV file, in hostComponent Bodies folder in Fusion360

    Input:
    . filename: full path and name of CSV file
    . hostComponent: look for planar anywhere in hostComponent folder.
    Return:
    . True when extrude was done, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, extrudeTuple = parse_csv_extrude_file(ui, title, filename)
    if not result:
        return False
    # Extract tuples, extrudeFilename is not used
    locationTuple, planarTuple, extentTuple, operationTuple = extrudeTuple
    _, groupComponentName = locationTuple
    profileSketchName, textSketchName, fromBodyName, planarIndices = planarTuple
    offset, taperAngles, extentType, distanceVales, toBodyName = extentTuple
    operation, participantBodyNames, resultBodyNames = operationTuple

    # Create groupComponent in hostComponent for extruded bodies objects, if
    # it does not already exist, else use hostComponent if groupComponentName
    # is empty string or is the hostComponent.
    groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)

    # Find object planar to extrude anywhere in hostComponent
    objectTuple = _find_planars_to_extrude(ui, hostComponent,
                                           profileSketchName, textSketchName, fromBodyName, planarIndices)

    # Find participant bodies in hostComponent and update operationTuple
    participantBodies = []
    if operation in ['join', 'cut', 'intersect']:
        for bodyName in participantBodyNames:
            body = utilities360.find_body_anywhere(ui, hostComponent, bodyName)
            if not body:
                interface360.error_text(ui, 'Participant body %s not found' % bodyName)
                return False
            participantBodies.append(body)
    operationTuple = (operation, participantBodies, resultBodyNames)

    # Find to_object body in hostComponent and update extentTuple
    toBody = None
    if toBodyName:
        toBody = utilities360.find_body_anywhere(ui, hostComponent, toBodyName)
        if not toBody:
            interface360.error_text(ui, 'To object body %s not found' % toBodyName)
            return False
    extentTuple = (offset, taperAngles, extentType, distanceVales, toBody)

    # Perform the extrude feature
    extrudeResult = extrude_planars(ui, objectTuple, operationTuple, extentTuple)

    # Rename the body or bodies of the extrude
    result, resultBodies = _rename_result_bodies(ui, resultBodyNames, extrudeResult)
    if not result:
        interface360.error_text(ui, 'Rename result extrude bodies with %s failed' % str(resultBodyNames))
        return False

    # Move extruded bodies to the groupComponent, if the groupComponent is
    # another component then the parentComponent of the object.
    # . Use groupComponent in hostComponent for extruded bodies objects
    # . Get parentComponent of the object (sketch or fromBody), because that is
    #   where the resultBodies are. No need for the planars here.
    object, _ = objectTuple
    if groupComponent != object.parentComponent:
        groupOccurrence = utilities360.get_occurrence_anywhere(groupComponent)
        for body in resultBodies:
            utilities360.move_body_to_occurrence(body, groupOccurrence)

    interface360.print_text(ui, 'Extruded for ' + filename)
    return True


def _find_planars_to_extrude(ui, hostComponent, profileSketchName, textSketchName, fromBodyName, planarIndices):
    """Find planars to extrude.

    The planar can be one or more profiles, or texts or faces.

    Input:
    . hostComponent: look for planar anywhere in hostComponent folder.
    . planar type one of:
      . profileSketchName: When != '' look for profiles in sketch
      . textSketchName:  When != '' look for texts in sketch
      . fromBodyName:  When != '' look for faces on from body
    . planarIndices: List of item indices

    Return:
    . objectTuple: Object (sketch or from body) and collection of planars
        (profiles, texts or faces), or None.

    Uses ui to report faults via Fusion360 GUI.
    """
    objectTuple = None
    if profileSketchName:
        # Get profiles in sketch to determine profile objectTuple
        sketch = utilities360.find_sketch_anywhere(ui, hostComponent, profileSketchName)
        if not sketch:
            interface360.error_text(ui, 'Sketch %s for profile not found' % profileSketchName)
            return False
        profiles = utilities360.get_sketch_profiles_collection(ui, sketch, planarIndices)
        if not profiles:
            return False
        objectTuple = (sketch, profiles)
    elif textSketchName:
        # Get texts in sketch to determine text objectTuple
        sketch = utilities360.find_sketch_anywhere(ui, hostComponent, textSketchName)
        if not sketch:
            interface360.error_text(ui, 'Sketch %s for text not found' % textSketchName)
            return False
        texts = utilities360.get_sketch_texts_collection(ui, sketch, planarIndices)
        if not texts:
            return False
        objectTuple = (sketch, texts)
    elif fromBodyName:
        # Get faces in body to determine face objectTuple
        fromBody = utilities360.find_body_anywhere(ui, hostComponent, fromBodyName)
        if not fromBody:
            interface360.error_text(ui, 'From body %s not found' % fromBodyName)
            return False
        faces = utilities360.get_body_faces_collection(ui, fromBody, planarIndices)
        if not faces:
            return False
        objectTuple = (fromBody, faces)
    return objectTuple


def _rename_result_bodies(ui, resultBodyNames, extrudeResult):
    """Rename bodies in extrudeResult with names from resultBodyNames

    Input:
    . resultBodyNames: if list is empty, then keep default names, else use
      names from list to rename the bodies in extrudeResult. If resultBodyNames
      contains not the same amount of names as the number of bodies in
      extrudeResult, then report error via ui.
    . extrudeResult: result feature of extrude

    Return:
    . result: True when rename went OK, else False
    . resultBodies: list of extrude result body objects

    Uses ui to report faults via Fusion360 GUI.
    """
    resultFalse = (False, None)
    resultBodies = []
    nofResultBodyNames = len(resultBodyNames)
    if nofResultBodyNames > 0:
        if len(resultBodyNames) == extrudeResult.bodies.count:
            # Rename the body or bodies of the extrude
            for bi in range(extrudeResult.bodies.count):
                body = extrudeResult.bodies.item(bi)
                body.name = resultBodyNames[bi]
                resultBodies.append(body)
            return (True, resultBodies)
        else:
            # Report actual extrude body names
            interface360.error_text(ui, 'extrude resultBodyNames = ' + str(resultBodyNames))
            interface360.error_text(ui, 'extrude nofResultBodyNames %d != %d extrudeResult.bodies.count' %
                                    (nofResultBodyNames, extrudeResult.bodies.count))
            for bi in range(extrudeResult.bodies.count):
                body = extrudeResult.bodies.item(bi)
                interface360.error_text(ui, 'extrude body.name = ' + str(body.name))
            return resultFalse
    else:
        # Keep default body names of the extrude
        for bi in range(extrudeResult.bodies.count):
            body = extrudeResult.bodies.item(bi)
            resultBodies.append(body)
        return (True, resultBodies)


def extrudes_from_csv_files(ui, title, folderName, hostComponent):
    """Extrudes from CSV files in folder, in hostComponent in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: look for planar anywhere in hostComponent folder.
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
