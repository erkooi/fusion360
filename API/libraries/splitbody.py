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
. first line: 'split' as filetype
. second line: split_body, body name
. third line: split_plane, plane name
. splitted_bodies
.   - names for splitted bodies, determine splitted bodies order based on a
      trial run
. remove_bodies
.   - names of bodies to remove

The splitting tool is a plane.
The bodyToSplit is kept, this is achieved by first copying the bodyToSplit and
renaming it into the first split name. The other split results get the other
split names. The number of split names must match the number of split results.
Split results that are not needed can be removed.
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
      - splitBodyName: body name
      - splitPlaneName: plane name
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
        if len(lineArr) > 1:
            lineWord1 = lineArr[1]
        if li == 0:
            if lineWord0 != 'split':
                return resultFalse
        elif li == 1:
            # Read split_body
            if lineWord0 != 'split_body':
                ui.messageBox('Expected split_body instead of %s in %s' % (lineWord0, filename), title)
                return resultFalse
            splitBodyName = lineWord1
        elif li == 2:
            # Read split_plane
            if lineWord0 != 'split_plane':
                ui.messageBox('Expected split_plane instead of %s in %s' % (lineWord0, filename), title)
                return resultFalse
            splitPlaneName = lineWord1
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
            elif lineWord0 != '':
                if readSplittedBodies:
                    splittedBodiesNames.append(lineWord0)
                if readRemoveBodies:
                    removeBodiesNames.append(lineWord0)

    # Successfully reached end of file
    splitBodyTuple = (splitBodyName, splitPlaneName, splittedBodiesNames, removeBodiesNames)
    return (True, splitBodyTuple)


def split_body(ui, hostComponent, splitBody, splitPlane, splittedBodiesNames):
    """Split body using splitPlane into splitted bodies. Rename splitted bodies
       with splittedBodiesNames.

    Input:
    . hostComponent: host component with the bodies
    . splitBody: body to split
    . splitPlaneName: split tool plane
    . splittedBodiesNames: list of body names, must match number of splitted
    Return:
    . True when split body went ok, else False

    Uses ui report faults via Fusion360 GUI.
    """
    result = True

    # Copy splitBody, because it is used for one of the splitted bodies
    hostOccurrence = utilities360.get_last_occurrence(hostComponent)
    bodyToSplit = utilities360.copy_body(splitBody, hostOccurrence)

    # Prepare splitBodyFeatureInput.
    splitBodyFeatures = hostComponent.features.splitBodyFeatures
    splitBodyFeatureInput = splitBodyFeatures.createInput(bodyToSplit, splitPlane, isSplittingToolExtended=True)

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
    """Split body from CSV file, in hostComponent in Fusion360

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
    splitBodyName, splitPlaneName, splittedBodiesNames, removeBodiesNames = splitBodyTuple

    # Find split body in hostComponent Bodies folder
    splitBody = hostComponent.bRepBodies.itemByName(splitBodyName)
    if not splitBody:
        interface360.error_text(ui, 'Split body %s not found' % splitBodyName)
        return False

    # Find split plane in hostComponent Construction folder or in any sub component
    splitPlane = utilities360.find_plane(hostComponent, splitPlaneName)
    if not splitPlane:
        interface360.error_text(ui, 'Split plane %s not found' % splitPlaneName)
        return False

    # Split body
    result = split_body(ui, hostComponent, splitBody, splitPlane, splittedBodiesNames)
    if not result:
        return False

    # Remove bodies
    if len(removeBodiesNames) > 0:
        removeFeatures = hostComponent.features.removeFeatures
        for bodyName in removeBodiesNames:
            body = hostComponent.bRepBodies.itemByName(bodyName)
            if body:
                removeFeatures.add(body)
            else:
                interface360.error_text(ui, 'Remove body %s not found' % bodyName)
                return False
    return True


def split_bodies_from_csv_files(ui, title, folderName, hostComponent):
    """Split body from CSV files in folder, in hostComponent in Fusion360

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
            interface360.print_text(ui, 'Split body for ' + filename)
            split_body_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No split body CSV files in %s' % folderName, title)
