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
. first line: 'combine' as filetype, name object name of combined bodies
  result, name of the group component for the combined bodies result
. second line: 'operation', 'join', 'cut', 'intersect'
. combine_bodies
  - target body name, one first line
  - one or more tool body names, one per line
. remove_bodies
  - names of bodies to remove

  targetBodyName:
  . The target_body is kept. This is default when the combined object is a new
    component, else this is achieved by first copying the target body to the
    combine body if the object is a new body.

  toolBodyNames:
  . The tool_bodies are kept.

  The new body gets the combine name. If the object is a new component, then
  the new component also gets the combine name.
"""

import interfacefiles
import schemacsv360
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
      - combineResultName: object name of combined bodies, is name of the
        combine bodies file
      - groupComponentName: group component for the combined bodies object
      - operation: 'join', 'cut', or 'intersect'
      - targetBodyName: target body name
      - toolBodyNames: list of tool body names
      - removeBodiesNames: optional list of body names to remove

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for combine bodies
    resultFalse = (False, None)
    targetBodyName = ''
    toolBodyNames = []
    removeBodiesNames = []
    readTargetBody = False
    readToolBodies = False
    readRemoveBodies = False
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'combine':
                return resultFalse
            combineResultName = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
        elif li == 1:
            # Read combine operation
            if lineWord != 'operation':
                ui.messageBox('Expected combine operation instead of %s in %s' % (lineWord, filename), title)
                return resultFalse
            operation = lineArr[1]
            if operation not in interfacefiles.validCombineOperations:
                ui.messageBox('No valid combine operation %s in %s' % (operation, filename), title)
                return resultFalse
        else:
            # Read lists for:
            # . combine_bodies
            # . remove_bodies
            if lineWord == 'combine_bodies':
                readTargetBody = True
                readToolBodies = False
                readRemoveBodies = False
            elif lineWord == 'remove_bodies':
                readTargetBody = False
                readToolBodies = False
                readRemoveBodies = True
            else:
                if readTargetBody:
                    targetBodyName = lineWord
                    readTargetBody = False
                    readToolBodies = True
                elif readToolBodies:
                    toolBodyNames.append(lineWord)
                elif readRemoveBodies:
                    removeBodiesNames.append(lineWord)

    if targetBodyName == '' or len(toolBodyNames) == 0:
        ui.messageBox('Not enough bodies in %s' % filename, title)
        return resultFalse

    # Successfully reached end of file
    combineBodiesTuple = (combineResultName, groupComponentName, operation,
                          targetBodyName, toolBodyNames, removeBodiesNames)
    return (True, combineBodiesTuple)


def combine_bodies_into_new_component(groupComponent, targetBody, toolBodies, operation, combineResultName):
    """Combine bodies into new component in groupComponent.

    Input:
    . groupComponent: group component for combine bodies result
    . targetBody, toolBodies:
      * combineBody = result of targetBody operation toolBodies
      * Keep targetBody and keep toolBodies.
    . operation: combine operation from validCombineOperations
    . combineResultName : name for combineComponent and for combineBody in
      combineComponent.
    Return: None
    """
    # Prepare combineFeatureInput for result in new component.
    # . Can use target_body, because it is kept when result is in new component
    combineFeatures = groupComponent.features.combineFeatures
    combineFeatureInput = combineFeatures.createInput(targetBody, toolBodies)
    combineFeatureInput.operation = schemacsv360.get_feature_operation_enum(operation)
    combineFeatureInput.isKeepToolBodies = True

    # Create new component, it will appear in rootComponent
    combineFeatureInput.isNewComponent = True
    combineFeature = combineFeatures.add(combineFeatureInput)

    # Rename new component to combineResultName
    combineComponent = combineFeature.parentComponent
    combineComponent.name = combineResultName

    # Rename body in new component to combineResultName
    combineBody = combineComponent.bRepBodies.item(0)
    combineBody.name = combineResultName

    # Default new combineComponent occurrence is last in rootComponent.
    rootComponent = utilities360.get_root_component(groupComponent)
    rootOccurrenceList = rootComponent.allOccurrences
    combineOccurrence = rootOccurrenceList.item(rootOccurrenceList.count - 1)

    # Move new occurrence to groupOccurrence. The groupComponent is anywhere in
    # rootComponent.
    groupOccurrence = utilities360.get_occurrence_anywhere(groupComponent)
    utilities360.move_occurrence_into_occurrence(combineOccurrence, groupOccurrence)


def combine_bodies_into_new_body(groupComponent, targetBody, toolBodies, operation, combineResultName):
    """Combine bodies into new body in groupComponent.

    Input:
    . groupComponent: group component for combine bodies result
    . targetBody, toolBodies:
      * combineBody = targetBody operation toolBodies
      * Keep targetBody and keep toolBodies.
    . operation: combine operation from validCombineOperations
    . combineResultName: name for combineBody
    Return: None
    """
    # Copy target body in groupOccurrence, because it is used as result for
    # combine body.
    groupOccurrence = utilities360.get_occurrence_anywhere(groupComponent)
    combineBody = utilities360.copy_body_to_occurrence(targetBody, groupOccurrence)

    # Prepare combineFeatureInput for result in new body.
    combineFeatures = groupComponent.features.combineFeatures
    combineFeatureInput = combineFeatures.createInput(combineBody, toolBodies)
    combineFeatureInput.operation = schemacsv360.get_feature_operation_enum(operation)
    combineFeatureInput.isKeepToolBodies = True

    # Create new body
    combineFeatureInput.isNewComponent = False
    combineFeatures.add(combineFeatureInput)

    # Rename new body
    combineBody.name = combineResultName


def combine_bodies_from_csv_file(ui, title, filename, hostComponent, combineNewComponent=False):
    """Combine bodies from CSV file, in Fusion360.

    Dependent on the groupComponentName the combined body will be put in the
    Bodies folder of hostComponent or hostComponent/groupComponent.

    Input:
    . filename: full path and name of CSV file
    . hostComponent: with the target body and tool bodies in Bodies folder and
      place the combined body in groupComponent Bodies folder.
    . combineNewComponent: when True create new component in hostComponent,
      else create new body in hostComponent Bodies folder
    Return:
    . True when new combine object was created, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, combineBodiesTuple = parse_csv_combine_bodies_file(ui, title, filename)
    if not result:
        return False
    combineResultName, groupComponentName, operation, \
        targetBodyName, toolBodyNames, removeBodiesNames = combineBodiesTuple

    # Find target body object and tool body objects anywhere in hostComponent
    targetBody = utilities360.find_body_anywhere(ui, hostComponent, targetBodyName)
    if not targetBody:
        interface360.error_text(ui, 'Target body not found in path of body name %s and not in %s' %
                                (targetBodyName, hostComponent.name))
        return False

    result, toolBodies = utilities360.find_bodies_collection_anywhere(ui, hostComponent, toolBodyNames)
    if not result:
        return False

    # Create groupComponent in hostComponent for combined body, if it does
    # not already exist, else use hostComponent if groupComponentName is empty
    # string or is the hostComponent.
    groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)

    # Create combined body and put result in new component in groupComponent
    # or in bodies of groupComponent.
    if combineNewComponent:
        combine_bodies_into_new_component(hostComponent, targetBody, toolBodies, operation, combineResultName)
    else:
        combine_bodies_into_new_body(groupComponent, targetBody, toolBodies, operation, combineResultName)

    # Remove bodies
    utilities360.remove_bodies_anywhere(ui, hostComponent, removeBodiesNames)
    interface360.print_text(ui, 'Combined bodies for ' + filename)
    return True


def combine_bodies_from_csv_files(ui, title, folderName, hostComponent, combineNewComponents=False):
    """Combine bodies from CSV files in folder, in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: with the target body and tool bodies in Bodies folder and
      place the combined body in hostComponent Bodies folder.
    . combineNewComponent: when True create new component in hostComponent,
      else create new body in hostComponent Bodies folder
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Combine bodies from CSV file in hostComponent
            combine_bodies_from_csv_file(ui, title, filename, hostComponent, combineNewComponents)
    else:
        ui.messageBox('No combine bodies CSV files in %s' % folderName, title)
