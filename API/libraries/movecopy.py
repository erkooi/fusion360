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
# Date: 16 jul 2023
"""Module to move, copy or transform object defined in a csv file in Fusion360.

The move, remove or copy operation is in the design hierarchy.
The translate or rotate transform operation is in the design 3D space.

Movecopy CSV file format:
. first line: 'movecopy' as filetype, name of movecopy file. The results are
  placed in the hostComponent or in the targetComponentName. Therefore there
  is no groupComponent option.
. second line: resolution 'mm' or 'cm'
. next lines: series of one or more operations from validMovecopyOperations:
  - Place object in design folders hierarchy:
    . 'move', objectType, objectName, targetComponentName
    . 'copy', objectType, objectName, copyName, optional targetComponentName
    . 'remove', objectType, objectName
    . 'light_bulb', objectType, objectName, 'on' or 'off'
  - Transform object in design 3D space:
    # translation vector in resolution units
    . 'translate', objectType, objectName, tx, ty, tz
    # rotation axis vector and rotation angle in degrees
    . 'rotate', objectType, objectName, ax, ay, az, angle
    If the transform has zero translation vector, or zero rotation axis, or
    zero rotation angle, then the operation is ignored and replaced by 'nop'
    to indicate no operation.
Fields:
. objectType: object type from validMovecopyObjects: 'component' or 'body'.
. objectName: name of input object in format:
  - <objectName>, search for object anywhere in host component
  - <componentName/objectName>, search for object anywhere in component with
    componentName
. copyName: plain name of copied component or body
"""

import interfacefiles
import interface360
import utilities360
import schemacsv360


def parse_csv_movecopy_file(ui, title, filename):
    """Parse move copy CSV file.

    Reads movecopy object from csv file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid movecopyTuple, else False with None
    . movecopyTuple:
      - movecopyFilename: name of the movecopy file
      - movecopyOperationTuples[]: list of one or more movecopy operations,
        each with:
        . objectType: 'component' or 'body' in validMovecopyObjects
        . objectName: component name or body name
        . an hierarchical or 3D movecopy operation from validMovecopyOperations:
          - 'move', with targetComponentName
          - 'copy', with copyName and optional targetComponentName
          - 'remove'
          - 'light_bulb'
          - 'translate', with translation vector3D
          - 'rotate', with rotation axis vector3D and angle

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for movecopy
    resultFalse = (False, None)
    movecopyOperationTuples = []
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'movecopy':
                return resultFalse
            movecopyFilename = lineArr[1]
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
                ui.messageBox('Use targetComponentName instead of groupComponentName %s for movecopy in %s' %
                              (groupComponentName, filename), title)
                return resultFalse
        elif li == 1:
            # Read units
            result, scale = schemacsv360.read_units(ui, title, filename, lineWord)
            if not result:
                return resultFalse
        else:
            # Read operations list
            result, operationTuple = _parse_operation(ui, title, filename, scale, lineArr)
            if not result:
                return resultFalse
            movecopyOperationTuples.append(operationTuple)

    # Successfully reached end of file
    movecopyTuple = (movecopyFilename, movecopyOperationTuples)
    return (True, movecopyTuple)


def _parse_operation(ui, title, filename, scale, lineArr):
    """Parse lineArr for operation and parameters.

    Input:
    . filename: full path and name of CSV file
    . scale: scale factor between lineArr values unit and API cm unit
    . lineArr: list of csv entries from a line

    Return:
    . result: True when valid operationTuple, else False. An invalid tranform
      is ignored and replaced by 'nop' to indicate no operation.
    . operationTuple:
      - movecopyOperation: movecopy operation from validMovecopyOperations
      - objectType: 'component' or 'body' in validMovecopyObjects
      - objectName: component name or body name
      - copyName: name of copied component or body
      - targetComponentName: name of target component for move or copy
      - lightBulbOn: switch object light bulb 'on' or 'off'
      - vector3D: translation vector or rotation axis vector
      - angle: rotation angle around rotation axis vector

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    resultFalse = (False, None)
    # Get parameters
    copyName = ''
    targetComponentName = ''
    lightBulbOn = True
    vector3D = None
    angle = 0.0
    try:
        # Read the movecopy operation
        movecopyOperation = lineArr[0]
        if movecopyOperation not in interfacefiles.validMovecopyOperations:
            ui.messageBox('No valid movecopy operation %s in %s' % (movecopyOperation, filename), title)
            return resultFalse
        # Read object info for the movecopy operation
        # . objectType
        objectType = lineArr[1]
        if objectType not in interfacefiles.validMovecopyObjects:
            ui.messageBox('No valid movecopy object type in %s' % filename, title)
            return resultFalse
        # . objectName
        objectName = lineArr[2]
        # Parse the movecopy operation
        if movecopyOperation == 'move':
            # . targetComponentName
            targetComponentName = lineArr[3]  # mandatory for move
        elif movecopyOperation == 'copy':
            # . copyName and optional targetComponentName
            copyName = lineArr[3]
            if len(lineArr) > 4:
                targetComponentName = lineArr[4]  # optional for copy
        elif movecopyOperation == 'remove':
            pass  # no additional arguments for remove
        elif movecopyOperation == 'light_bulb':
            lightBulbOn = True if lineArr[3] == 'on' else False
        elif movecopyOperation in ['translate', 'rotate']:
            # . vector3D
            result, vector3D = schemacsv360.get_3d_vector(ui, title, filename, scale, lineArr[3:6])
            if not result:
                movecopyOperation = 'nop'
            # . angle
            angle = 0.0
            if movecopyOperation == 'rotate':
                result, angle = schemacsv360.get_rotation_angle(ui, title, filename, lineArr[6])
                if not result:
                    movecopyOperation = 'nop'
    except Exception:
        ui.messageBox('No valid movecopy transform in %s' % filename, title)
        return resultFalse
    operationTuple = (movecopyOperation, objectType, objectName, copyName, targetComponentName,
                      lightBulbOn, vector3D, angle)
    return (True, operationTuple)


def movecopy_from_csv_file(ui, title, filename, hostComponent):
    """Movecopy object from CSV file, in hostComponent in Fusion360.

    Input:
    . filename: full path and name of CSV file
    . hostComponent: host component with the input object for movecopy
    Return:
    . True when the object operations went ok, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, movecopyTuple = parse_csv_movecopy_file(ui, title, filename)
    if not result:
        return False
    # The movecopyFilename in movecopyTuple is not used
    _, movecopyOperationTuples = movecopyTuple

    # Perform the list of movecopy operations
    for operationTuple in movecopyOperationTuples:
        movecopyOperation, objectType, objectName, copyName, targetComponentName, \
            lightBulbOn, vector3D, angle = operationTuple
        if objectType == 'component':
            objectOccurrence = _find_object_to_movecopy(ui, hostComponent, objectType, objectName)
            objectComponent = objectOccurrence.component
            if movecopyOperation == 'move':
                targetOccurrence = utilities360.find_or_create_occurrence(ui, hostComponent, targetComponentName)
                objectOccurrence = utilities360.move_occurrence_into_occurrence(objectOccurrence, targetOccurrence)
            elif movecopyOperation == 'copy':
                targetOccurrence = utilities360.find_or_create_occurrence(ui, hostComponent, targetComponentName)
                objectOccurrence = utilities360.copy_component_as_new_into_occurrence(objectComponent, targetOccurrence)
                # Changing occurrence.component.name also changes occurrence.name
                objectOccurrence.component.name = copyName
                objectOccurrence.isLightBulbOn = False  # default make inactive copy at same location
            elif movecopyOperation == 'remove':
                utilities360.remove_occurrence(objectOccurrence)
            elif movecopyOperation == 'light_bulb':
                objectOccurrence.isLightBulbOn = lightBulbOn
            elif movecopyOperation in ['translate', 'rotate']:
                transformTuple = (movecopyOperation, vector3D, angle)
                utilities360.transform_occurrence(ui, objectOccurrence, transformTuple)
            elif movecopyOperation == 'nop':
                pass
            else:
                return False
        else:  # body
            objectBody = _find_object_to_movecopy(ui, hostComponent, objectType, objectName)
            if movecopyOperation == 'move':
                targetOccurrence = utilities360.find_or_create_occurrence(ui, hostComponent, targetComponentName)
                objectBody = utilities360.move_body_to_occurrence(objectBody, targetOccurrence)
            elif movecopyOperation == 'copy':
                targetOccurrence = utilities360.find_or_create_occurrence(ui, hostComponent, targetComponentName)
                objectBody = utilities360.copy_body_to_occurrence(objectBody, targetOccurrence)
                objectBody.name = copyName
                objectBody.isLightBulbOn = False  # default make inactive copy at same location
            elif movecopyOperation == 'remove':
                utilities360.remove_body(objectBody)
            elif movecopyOperation == 'light_bulb':
                objectBody.isLightBulbOn = lightBulbOn
            elif movecopyOperation in ['translate', 'rotate']:
                transformTuple = (movecopyOperation, vector3D, angle)
                utilities360.transform_body(ui, objectBody, transformTuple)
            elif movecopyOperation == 'nop':
                pass
            else:
                return False
    interface360.print_text(ui, 'Moved or copied for ' + filename)
    return True


def _find_object_to_movecopy(ui, hostComponent, objectType, objectName):
    """Find input object to movecopy.

    Search anywhere in optional component specified in objectName, or otherwise
    anywhere in the hostComponent.

    Input:
      - hostComponent: search for object anywhere in hostComponent
      - objectType: 'component' or 'body' in validMovecopyObjects
      - objectName: component name or body name, with optional search component
        name
    Return:
    - objectOccurrence or objectBody when objectName is found, else False:
      . objectOccurrence: occurrence object when objectType == 'component'
      . objectBody: body object when objectType == 'body'

    Uses ui to interact with user and report faults via Fusion360 GUI.
    """
    # Find object to movecopy
    if objectType == 'component':
        # Find component objectName
        occurrences = utilities360.find_occurrences_anywhere(hostComponent, objectName)
        if len(occurrences) == 0:
            interface360.error_text(ui,
                                    'Object component not found in path of object name %s, '
                                    'and not in host component %s' %
                                    (objectName, hostComponent.name))
            return False
        objectOccurrence = occurrences[0]
        return objectOccurrence
    else:  # body
        # Find body objectName
        objectBody = utilities360.find_body_anywhere(ui, hostComponent, objectName)
        if not objectBody:
            interface360.error_text(ui,
                                    'Object body not found in path of object name %s, '
                                    'and not in host component %s' %
                                    (objectName, hostComponent.name))
            return False
        return objectBody


def movecopy_from_csv_files(ui, title, folderName, hostComponent):
    """Movecopy object from CSV files in folder, in hostComponent in Fusion360.

    Input:
    . folderName: full path and folder name of CSV files
    . hostComponent: host component with the objects to move
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Move or copy object from CSV file in hostComponent
            movecopy_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No move or copy CSV files in %s' % folderName, title)
