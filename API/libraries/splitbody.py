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
"""Module to split body defined in a csv file in Fusion360.

Split body CSV file format:
. comment lines or comment in line will be removed
. first line: 'split' as filetype, name of the split body file, name of the
  group component for the splitted bodies.
. second line: split_body, body name
. third line, split tool can one from validSplitToolType:
  - split_tool, plane, plane name
  - split_tool, body, body name
. splitted_bodies
  - names for splitted bodies, determine splitted bodies order based on a
    trial run
. remove_bodies
  - names of bodies to remove

The split body and split tool are searched for anywhere in the host component.
The split tool is a plane or a body.
The split body is kept, this is achieved by first copying it to bodyToSplit and
renaming it into the first splitted_bodies name. The other split results get
the other splitted_bodies names. The number of splitted_bodies names must match
the number of split results. Splitted bodies results that are not needed can be
removed via remove_bodies.
"""

import interfacefiles
import interface360
import utilities360


def parse_csv_split_body_file(ui, title, filename):
    """Parse split body CSV file.

    Reads body to split and split tool plane from csv file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid splitBodyTuple, else False with None
    . splitBodyTuple:
      - splitBodyFilename: name of the split body file
      - groupComponentName: group component for the splitted bodies objects
      - splitBodyName: body name
      - splitToolName: plane name
      - splittedBodiesNames: list of body names, must match number of splitted
        bodies that result after split body
      - removeBodiesNames: list of body names, can be empty

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for split body
    resultFalse = (False, None)
    splittedBodiesNames = []
    removeBodiesNames = []
    readSplittedBodies = False
    readRemoveBodies = False
    for li, lineArr in enumerate(lineLists):
        lineWord0 = lineArr[0]
        if li == 0:
            if lineWord0 != 'split':
                return resultFalse
            splitBodyFilename = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
        elif li == 1:
            # Read split_body
            if lineWord0 != 'split_body':
                ui.messageBox('Expected split_body instead of %s in %s' % (lineWord0, filename), title)
                return resultFalse
            splitBodyName = lineArr[1]
        elif li == 2:
            # Read split_tool
            if lineWord0 != 'split_tool':
                ui.messageBox('Expected split_tool instead of %s in %s' % (lineWord0, filename), title)
                return resultFalse
            splitToolType = lineArr[1]
            if splitToolType not in interfacefiles.validSplitToolTypes:
                ui.messageBox('Unexpected split_tool type %s in %s' % (splitToolType, filename), title)
                return resultFalse
            splitToolName = lineArr[2]
        else:
            # Read lists for:
            # . splitted_bodies
            # . remove_bodies
            if lineWord0 == 'splitted_bodies':
                readSplittedBodies = True
                readRemoveBodies = False
            elif lineWord0 == 'remove_bodies':
                readSplittedBodies = False
                readRemoveBodies = True
            else:
                if readSplittedBodies:
                    splittedBodiesNames.append(lineWord0)
                if readRemoveBodies:
                    removeBodiesNames.append(lineWord0)

    # Successfully reached end of file
    splitBodyTuple = (splitBodyFilename, groupComponentName, splitBodyName,
                      splitToolType, splitToolName, splittedBodiesNames, removeBodiesNames)
    return (True, splitBodyTuple)


def split_body(ui, hostComponent, groupComponent, splitBody, splitTool, splittedBodiesNames):
    """Split body using splitTool into splitted bodies. Rename splitted bodies
       with splittedBodiesNames.

    Input:
    . hostComponent: host component with the splitBody and splitTool
    . groupComponent: group component for splitted bodies
    . splitBody: body to split
    . splitTool: split tool
    . splittedBodiesNames: list of body names, must match number of splitted
    Return:
    . True when split body went ok, else False

    Uses ui report faults via Fusion360 GUI.
    """
    result = True

    # Copy splitBody, because it is used for one of the splitted bodies.
    groupOccurrence = utilities360.get_occurrence_anywhere(groupComponent)
    bodyToSplit = utilities360.copy_body_to_occurrence(splitBody, groupOccurrence)

    # Prepare splitBodyFeatureInput.
    splitBodyFeatures = hostComponent.features.splitBodyFeatures
    splitBodyFeatureInput = splitBodyFeatures.createInput(bodyToSplit, splitTool, isSplittingToolExtended=True)

    # Split the body
    splitBodyFeature = splitBodyFeatures.add(splitBodyFeatureInput)

    # Rename splitted bodies
    splittedBodies = splitBodyFeature.bodies
    expectedNofBodies = len(splittedBodiesNames)
    if splittedBodies.count == expectedNofBodies:
        for sb in range(splittedBodies.count):
            splittedBodies.item(sb).name = splittedBodiesNames[sb]
    else:
        interface360.error_text(
            ui, 'Unexpected number of splitted bodies: %d != %d' % (splittedBodies.count, expectedNofBodies))
        result = False
    return result


def split_body_from_csv_file(ui, title, filename, hostComponent):
    """Split body from CSV file, in Fusion360

    Dependent on the groupComponentName the splitted body will be put in the
    Bodies folder of hostComponent or hostComponent/groupComponent.

    Input:
    . filename: full path and name of CSV file
    . hostComponent: host component with the body to split
    Return:
    . True when splitted bodies were created, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, splitBodyTuple = parse_csv_split_body_file(ui, title, filename)
    if not result:
        return False
    splitBodyFilename, groupComponentName, splitBodyName, splitToolType, splitToolName, \
        splittedBodiesNames, removeBodiesNames = splitBodyTuple

    # Find split body anywhere in hostComponent
    splitBody = utilities360.find_body_anywhere(ui, hostComponent, splitBodyName)
    if not splitBody:
        interface360.error_text(ui, 'Split body %s not found in host component %s' %
                                (splitBodyName, hostComponent.name))
        return False

    # Find split tool anywhere in hostComponent component
    if splitToolType == 'plane':
        splitTool = utilities360.find_plane_anywhere(ui, hostComponent, splitToolName)
        if not splitTool:
            interface360.error_text(ui, 'Split tool plane %s not found in host component %s' %
                                    (splitToolName, hostComponent.name))
            return False
    elif splitToolType == 'body':
        splitTool = utilities360.find_body_anywhere(ui, hostComponent, splitToolName)
        if not splitTool:
            interface360.error_text(ui, 'Split tool body %s not found in host component %s' %
                                    (splitToolName, hostComponent.name))
            return False
    else:
        return False

    # Create groupComponent in hostComponent for split body object, if it does
    # not already exist, else use hostComponent if groupComponentName is empty
    # string or is the hostComponent.
    groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)

    # Split body and put result in groupComponent
    result = split_body(ui, hostComponent, groupComponent, splitBody, splitTool, splittedBodiesNames)
    if not result:
        return False

    # Remove bodies
    result = utilities360.remove_bodies_anywhere(ui, hostComponent, removeBodiesNames)
    if not result:
        return False
    interface360.print_text(ui, 'Splitted body for ' + filename)
    return True


def split_bodies_from_csv_files(ui, title, folderName, hostComponent):
    """Split body from CSV files in folder, in Fusion360

    Input:
    . folderName: full path and folder name of CSV files
    . hostComponent: host component with the body to split
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Split body from CSV file in hostComponent
            split_body_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No split body CSV files in %s' % folderName, title)
