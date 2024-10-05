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
# Date: 3 oct 2024
"""Module to modify edges of bodies defined in a csv file in Fusion360.

The edges can modified with a fillet or a chamfer.

Modify edges CSV file format:
. first line: 'modifyedges' as filetype, name of modifyedges file. The
  modifications are applied to edges of existing bodies, so there is no new
  object and therefore no groupComponent option.
. second line: resolution 'mm' or 'cm'
. next lines: series of one or more edge modifications from
     validModifyEdgesOperations:
  . 'log_faces', bodyName
  . 'log_edges', bodyName
  . 'fillet', bodyName, radius, 'edges', edgeIndices
  . 'fillet', bodyName, radius, 'faces', faceIndices
  . 'chamfer', bodyName, distance, angle, 'edges', edgeIndices
  . 'chamfer', bodyName, distance, angle, 'faces', faceIndices

With radius and distance in resolution units and angle in degrees.

Look for bodyName in hostComponent or in optional specific body search
component name in the bodyName, separated by a slash.
"""

import math
import adsk.fusion

import interfacefiles
import interface360
import utilities360
import schemacsv360


def parse_csv_modifyedges_file(ui, title, filename):
    """Parse modify edges CSV file.

    Reads modifyedges object from csv file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid modifyedgesTuple, else False with None
    . modifyedgesTuple:
      - modifyedgesFilename: name of the modifyedges file
      - modifyedgesOperationTuples[]: list of one or more modifyedges
        operations.

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for modifyedges
    resultFalse = (False, None)
    modifyedgesOperationTuples = []
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'modifyedges':
                return resultFalse
            modifyedgesFilename = lineArr[1]
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
                ui.messageBox('Do not use groupComponentName %s for modifyedges in %s' %
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
            modifyedgesOperationTuples.append(operationTuple)

    # Successfully reached end of file
    modifyedgesTuple = (modifyedgesFilename, modifyedgesOperationTuples)
    return (True, modifyedgesTuple)


def _parse_operation(ui, title, filename, scale, lineArr):
    """Parse lineArr for operation and parameters.

    Input:
    . filename: full path and name of CSV file
    . scale: scale factor between lineArr values unit and API cm unit
    . lineArr: list of csv entries from a line

    Return:
    . result: True when valid operationTuple, else False.
    . operationTuple:
      . modifyedgesOperation: operation in validModifyEdgesOperations
      . bodyName: component name or body name
      . size: radius for fillet, or distance for chamfer
      . angle: angle for chamfer
      . itemSelect: use 'faces' to define edges or use 'edges' to directly
        specify the edges
      . itemIndices: list of one or more indices of faces or edges

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    resultFalse = (False, None)
    # Get parameters
    bodyName = ''
    size = 0
    angle = 0
    itemSelect = ''
    itemIndices = []
    try:
        # Read the modifyedges operation
        modifyedgesOperation = lineArr[0]
        if modifyedgesOperation not in interfacefiles.validModifyEdgesOperations:
            ui.messageBox('No valid modifyedges operation %s in %s' % (modifyedgesOperation, filename), title)
            return resultFalse
        # Parse the modifyedges operation
        bodyName = lineArr[1]
        if modifyedgesOperation == 'fillet':
            size = float(lineArr[2]) * scale
            itemSelect = lineArr[3]
            itemIndices = interfacefiles.convert_entries_to_integers(lineArr[4:])
        elif modifyedgesOperation == 'chamfer':
            size = float(lineArr[2]) * scale
            angle = float(lineArr[3])
            itemSelect = lineArr[4]
            itemIndices = interfacefiles.convert_entries_to_integers(lineArr[5:])
        if itemSelect and itemSelect not in interfacefiles.validModifyEdgesItems:
            ui.messageBox('No valid modifyedges item %s in %s' % (itemSelect, filename), title)
            return resultFalse
    except Exception:
        ui.messageBox('No valid modifyedges operation in %s' % filename, title)
        return resultFalse
    operationTuple = (modifyedgesOperation, bodyName, size, angle, itemSelect, itemIndices)
    return (True, operationTuple)


def modifyedges_from_csv_file(ui, title, filename, hostComponent):
    """Modifyedges of bodies from CSV file, in hostComponent in Fusion360.

    Input:
    . filename: full path and name of CSV file
    . hostComponent: host component with the bodies for modifyedges
    Return:
    . True when the modifyedges operations went ok, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file
    result, modifyedgesTuple = parse_csv_modifyedges_file(ui, title, filename)
    if not result:
        return False
    # The modifyedgesFilename in modifyedgesTuple is not used
    _, modifyedgesOperationTuples = modifyedgesTuple

    # Perform the list of modifyedges operations
    for operationTuple in modifyedgesOperationTuples:
        modifyedgesOperation, bodyName, size, angle, itemSelect, itemIndices = operationTuple
        body = utilities360.find_body_anywhere(ui, hostComponent, bodyName)
        if not body:
            interface360.error_text(ui, 'Body not found in path of body name %s, and not in host component %s' %
                                    (bodyName, hostComponent.name))
            return False
        if modifyedgesOperation == 'log_faces':
            utilities360.log_body_faces(ui, body, bodyName)
        elif modifyedgesOperation == 'log_edges':
            utilities360.log_body_edges(ui, body, bodyName)
        elif modifyedgesOperation == 'fillet':
            apply_fillets(ui, body, size, itemSelect, itemIndices)
        elif modifyedgesOperation == 'chamfer':
            apply_chamfers(ui, body, size, angle, itemSelect, itemIndices)
        else:
            return False
    interface360.print_text(ui, 'Modified edges for ' + filename)
    return True


def apply_fillets(ui, body, radius, itemSelect, itemIndices):
    """Apply fillet with radius to edges of body.
    """
    # Collect edges
    edgeCollection = utilities360.get_body_edges_collection(ui, body, itemSelect, itemIndices)

    # Prepare fillet
    radiusInput = adsk.core.ValueInput.createByReal(radius)
    isTangentChain = True
    filletFeatures = body.parentComponent.features.filletFeatures
    filletFeatureInput = filletFeatures.createInput()
    filletFeatureInput.isRollingBallCorner = True
    filletFeatureInput.edgeSetInputs.addConstantRadiusEdgeSet(edgeCollection, radiusInput, isTangentChain)

    # Apply fillet
    filletResult = filletFeatures.add(filletFeatureInput)
    return filletResult


def apply_chamfers(ui, body, distance, angle, itemSelect, itemIndices):
    """Apply chamfer with distance to edges of body.
    """
    # Collect edges
    edgeCollection = utilities360.get_body_edges_collection(ui, body, itemSelect, itemIndices)
    interface360.print_text(ui, 'edgeCollection ' + str(edgeCollection.count))

    # Prepare chamfer
    distanceInput = adsk.core.ValueInput.createByReal(distance)
    angleInput = adsk.core.ValueInput.createByReal(math.radians(angle))
    isFlipped = False
    isTangentChain = True
    chamferFeatures = body.parentComponent.features.chamferFeatures
    chamferFeatureInput = chamferFeatures.createInput2()
    chamferFeatureInput.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(
        edgeCollection, distanceInput, angleInput, isFlipped, isTangentChain)

    # Apply chamfer
    chamferResult = chamferFeatures.add(chamferFeatureInput),
    return chamferResult


def modifyedges_from_csv_files(ui, title, folderName, hostComponent):
    """Modifyedges object from CSV files in folder, in hostComponent in Fusion360.

    Input:
    . folderName: full path and folder name of CSV files
    . hostComponent: host component with bodies for modifyedges
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Modifyedges of bodies from CSV file in hostComponent
            modifyedges_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No modifyedges CSV files in %s' % folderName, title)
