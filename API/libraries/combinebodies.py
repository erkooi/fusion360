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
"""Module to combine bodies defined in a csv file into a new body or new
   component in Fusion360.

Combine bodies CSV file format:
. comment lines or comment in line will be removed
. first line: 'combine' as filetype
. second line: combine name of combined bodies
. third line: operation 'join', 'cut', 'intersect'
. target_body, body name
. tool_bodies
  - one or more tool body names  # one per line

The tool_bodies are kept.
The target_body is kept. This is default when the combined object is a new
component, else this is achieved by first copying the target body to the
combine body if the object is a new body.
The new body gets the combine name. If the object is a new component, then the
new component also gets the combine name.

"""

import interfacefiles
import interface360
import utilities360


def parse_csv_combine_bodies_file(ui, title, filename):
    """Parse combine bodies CSV file.

    Reads bodies from csv file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid combineBodiesTuple, else False with none
    . combineBodiesTuple:
      - combineName: object name of combined bodies
      - operation: 'join', 'cut', or 'intersect'
      - targetBodyName: target body name
      - toolBodyNames: list of tool body names

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for combine bodies
    resultFalse = (False, None)
    for li, lineArr in enumerate(lineLists):
        lineWord0 = lineArr[0]
        if len(lineArr) > 1:
            lineWord1 = lineArr[1]
        if li == 0:
            if lineWord0 != 'combine':
                return resultFalse
        elif li == 1:
            # Read combineName
            combineName = lineWord0
        elif li == 2:
            # Read combine operation
            operation = lineWord0
            if operation not in interfacefiles.validOperations:
                ui.messageBox('No valid combine operation %s in %s' % (operation, filename), title)
                return resultFalse
        elif li == 3:
            # Read target_body
            if lineWord0 != 'target_body':
                ui.messageBox('Expected target_body instead of %s in %s' % (lineWord0, filename), title)
                return resultFalse
            targetBodyName = lineWord1
        elif li == 4:
            # Read tool_bodies
            if lineWord0 != 'tool_bodies':
                ui.messageBox('Expected tool_bodies instead of %s in %s' % (lineWord0, filename), title)
                return resultFalse
            toolBodyNames = []
        else:
            # Read tool body names
            if lineWord0 != '':
                toolBodyNames.append(lineWord0)

    if len(toolBodyNames) == 0:
        ui.messageBox('No tool bodies in %s' % filename, title)
        return resultFalse

    # Successfully reached end of file
    combineBodiesTuple = (combineName, operation, targetBodyName, toolBodyNames)
    return (True, combineBodiesTuple)


def combine_bodies_into_new_component(hostComponent, targetBody, toolBodies, operation, combineName):
    """Combine bodies in hostComponent into new component or new body in hostComponent.

    Input:
    . hostComponent: host component with the target body and tool bodies
    . targetBody, toolBodies:
      * combineBody = result of targetBody operation toolBodies
      * Keep targetBody and keep toolBodies.
    . operation: combine operation from validOperations
    . combineName : name for combineComponent and for combineBody in combineComponent
    Return: None
    """
    # Prepare combineFeatureInput for result in new component.
    # . Can use target_body, because it is kept when result is in new component
    combineFeatures = hostComponent.features.combineFeatures
    combineFeatureInput = combineFeatures.createInput(targetBody, toolBodies)
    combineFeatureInput.operation = utilities360.get_feature_operation_enum(operation)
    combineFeatureInput.isKeepToolBodies = True

    # Create new component, it will appear in rootComponent
    combineFeatureInput.isNewComponent = True
    combineFeature = combineFeatures.add(combineFeatureInput)

    # Rename new component to combineName
    combineComponent = combineFeature.parentComponent
    combineComponent.name = combineName

    # Rename body in new component to combineName
    combineBody = combineComponent.bRepBodies.item(0)
    combineBody.name = combineName

    # Default new combineComponent occurrence is last in rootComponent.
    rootComponent = utilities360.get_root_component(hostComponent)
    rootOccurrenceList = rootComponent.allOccurrences
    combineOccurrence = rootOccurrenceList.item(rootOccurrenceList.count - 1)

    # Move new occurrence to hostOccurrence
    hostOccurrence = utilities360.get_last_occurrence(hostComponent)
    utilities360.move_occurrence(combineOccurrence, hostOccurrence)


def combine_bodies_into_new_body(hostComponent, targetBody, toolBodies, operation, combineName):
    """Combine bodies in hostComponent into new body in hostComponent.

    Input:
    . hostComponent: host component with the target body and tool bodies, and
      place for the combined body
    . targetBody, toolBodies:
      * combineBody = targetBody operation toolBodies
      * Keep targetBody and keep toolBodies.
    . operation: combine operation from validOperations
    . combineName: name for combineBody
    Return: None
    """
    # Copy target body in hostOccurrence, because it is used as result for combine body
    hostOccurrence = utilities360.get_last_occurrence(hostComponent)
    combineBody = utilities360.copy_body(targetBody, hostOccurrence)

    # Prepare combineFeatureInput for result in new body.
    combineFeatures = hostComponent.features.combineFeatures
    combineFeatureInput = combineFeatures.createInput(combineBody, toolBodies)
    combineFeatureInput.operation = utilities360.get_feature_operation_enum(operation)
    combineFeatureInput.isKeepToolBodies = True

    # Create new body
    combineFeatureInput.isNewComponent = False
    combineFeatures.add(combineFeatureInput)

    # Rename new body
    combineBody.name = combineName


def combine_bodies_from_csv_file(ui, title, filename, hostComponent, combineNewComponent=False, verbosity=False):
    """Combine bodies from CSV file, in hostComponent in Fusion360

    Input:
    . filename: full path and name of CSV file
    . hostComponent: with the target body and tool bodies in Bodies folder and
      place the combined body in hostComponent Bodies folder when
      combineNewComponent = False.
    . combineNewComponent: when True create new component in hostComponent,
      else create new body in hostComponent Bodies folder
    . verbosity: when False no print_text()
    Return:
    . True when new combine object was created, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, combineBodiesTuple = parse_csv_combine_bodies_file(ui, title, filename)
    if not result:
        return False
    combineName, operation, targetBodyName, toolBodyNames = combineBodiesTuple

    # Find body objects in hostComponent
    targetBody = hostComponent.bRepBodies.itemByName(targetBodyName)
    if not targetBody:
        interface360.error_text(ui, 'Target body %s not found' % targetBodyName)
        return False

    result, toolBodies = utilities360.find_bodies_collection(ui, hostComponent, toolBodyNames)
    if not result:
        return False

    # Create combine object
    if combineNewComponent:
        combine_bodies_into_new_component(hostComponent, targetBody, toolBodies, operation, combineName)
    else:
        combine_bodies_into_new_body(hostComponent, targetBody, toolBodies, operation, combineName)
    return True


def combine_bodies_from_csv_files(ui, title, folderName, hostComponent, combineNewComponents=False):
    """Combine bodies from CSV files in folder, in hostComponent in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: with the target body and tool bodies in Bodies folder and
      place the combined body in hostComponent Bodies folder when
      combineNewComponent = False.
    . combineNewComponent: when True create new component in hostComponent,
      else create new body in hostComponent Bodies folder
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Combine bodies from CSV file in hostComponent
            interface360.print_text(ui, 'Combine bodies for ' + filename)
            combine_bodies_from_csv_file(ui, title, filename, hostComponent, combineNewComponents)
    else:
        ui.messageBox('No combine bodies CSV files in %s' % folderName, title)
