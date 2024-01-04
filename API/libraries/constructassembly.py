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
"""Module to construct assembly from csv file into an assembly component in
Fusion360.

Assembly CSV file format:
. comment lines or comment in line will be removed
. first line: 'assembly' as filetype
. second line: assembly name of the assembly component
  - activate, and if necessary create, assembly component for design in csv/
    directory
  - component structure follows csv/ directory structure, so sub directory
    names in csv/ become group component names within the assembly component
  - filename paths and directory names are relative to csv/
  - support only one level of sub directory within csv/, so also one level of
    group component
. next lines:
  - one assembly action per line, order of actions defines the design process
  - object names have to be unique in whole assembly, so they can be referred
    to from anywhere in the assembly component without having to specify
    where they are located.
  - create objects in the Sketches, Bodies or Construction of the group
    component
  - assembly actions:
    . create_sketch, 'sketch csv filename path'
    . multiple_create_sketch, 'sketches csv directory name'
    . create_plane, 'plane csv filename path'
    . multiple_create_plane, 'planes csv directory name'
    . create_loft, 'loft csv filename path'
    . multiple_create_loft, 'lofts csv directory name'
    . run_extrude, 'extrude csv filename path'
    . multiple_run_extrude, 'extrudes csv directory name'
    . run_combine, 'combine_bodies csv filename path'
    . multiple_run_combine, 'combine_bodies csv directory name'
    . run_split, 'split_body csv filename path'
    . multiple_run_split, 'split_body csv directory name'
    . run_movecopy, 'movecopy csv filename path'
    . multiple_run_movecopy, 'movecopy csv directory name'

Remarks:
. Sketches and planes can be in seperate group components within the
  hostComponent, because they do not rely other objects and cvan be found
  from the hostComponent.
. Bodies need to be in the same groupComponent = hostComponent, because then
  the loft can find the sketches, and the combine can find the bodies, and the
  split can find the bodies and planes. Therefor use groupComponentName
  = assemblyComponentName in the assembly CSV file.
"""

import os.path

import interfacefiles
import interface360
import utilities360
import importsketch
import createplane
import createloft
import extrude
import combinebodies
import splitbody
import movecopy


def parse_csv_assembly_file(ui, title, assemblyFilename):
    """Parse assembly CSV file.

    Reads script actions from an assembly CSV file.

    Input:
    . assemblyFilename: full path and name of a assembly CSV file
    Return:
    . result: True when valid assemblyTuple, else False with none
    . assemblyTuple:
      - assemblyComponentName: name of the assembly component
      - actions: list of actionTuples
        . actionTuple:
          - action: assembly action from interfacefiles.validAssemblyActions.
          - locationName: sub directory name of action CSV files or sub
            directory name plus filename of one action CSV file.
          - groupComponentName: Optional group component name for action
            results. Default extract group component name from locationName.

    Uses ui, title, assemblyFilename to interact with user and report faults
    via Fusion360 GUI.
    """
    # Read assembly CSV file and remove comments and empty lines
    fileLines = interfacefiles.read_data_lines_from_file(assemblyFilename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for assembly sections
    resultFalse = (False, None)
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'assembly':
                return resultFalse
        elif li == 1:
            # Read assemblyComponentName
            assemblyComponentName = lineWord
            actions = []
        else:
            # Read assembly actions, one per line
            if lineWord not in interfacefiles.validAssemblyActions:
                ui.messageBox('Not a valid action %s in %s' % (lineWord, assemblyFilename), title)
                return resultFalse
            echoString, locationName, groupComponentName = ('', '', '')
            action = lineWord
            if action == 'echo':
                echoString = interfacefiles.convert_entries_to_single_string(lineArr[1:])
            else:
                locationName = lineArr[1]
                groupComponentName = interfacefiles.extract_component_name(locationName)
                if len(lineArr) > 2:
                    groupComponentName = lineArr[2]
                if not groupComponentName:
                    ui.messageBox('Missing group component name in %s' % assemblyFilename, title)
            actionTuple = (action, echoString, locationName, groupComponentName)
            actions.append(actionTuple)

    if len(actions) == 0:
        ui.messageBox('No actions in %s' % assemblyFilename, title)
        return resultFalse

    # Successfully reached end of file
    assemblyTuple = (assemblyComponentName, actions)
    return (True, assemblyTuple)


def perform_action(ui, title, fullLocationName, groupComponent, action):
    """Perform action in groupComponent

    Input:
    . action: Fusion 360 command, specified in CSV file
    . fullLocationName: full location name for CSV directory or file
    . groupComponent: group component name for action results

    Return: True when action is done, else False
    """
    # . Sketches and planes can be in seperate group components within the
    #   hostComponent.
    if action == 'create_sketch':
        importsketch.create_sketch_from_csv_file(ui, title, fullLocationName, groupComponent)
    elif action == 'multiple_create_sketch':
        importsketch.create_sketches_from_csv_files(ui, title, fullLocationName, groupComponent)
    elif action == 'create_plane':
        createplane.create_plane_from_csv_file(ui, title, fullLocationName, groupComponent)
    elif action == 'multiple_create_plane':
        createplane.create_planes_from_csv_files(ui, title, fullLocationName, groupComponent)

    # . Bodies need to be in the groupComponent = hostComponent, because
    #   they build upon on sketches, planes and bodies.
    elif action == 'run_extrude':
        extrude.extrude_from_csv_file(ui, title, fullLocationName, groupComponent)
    elif action == 'multiple_run_extrude':
        extrude.extrudes_from_csv_files(ui, title, fullLocationName, groupComponent)
    elif action == 'create_loft':
        createloft.create_loft_from_csv_file(ui, title, fullLocationName, groupComponent)
    elif action == 'multiple_create_loft':
        createloft.create_lofts_from_csv_files(ui, title, fullLocationName, groupComponent)
    elif action == 'run_combine':
        combinebodies.combine_bodies_from_csv_file(ui, title, fullLocationName, groupComponent)
    elif action == 'multiple_run_combine':
        combinebodies.combine_bodies_from_csv_files(ui, title, fullLocationName, groupComponent)
    elif action == 'run_split':
        splitbody.split_body_from_csv_file(ui, title, fullLocationName, groupComponent)
    elif action == 'multiple_run_split':
        splitbody.split_bodies_from_csv_files(ui, title, fullLocationName, groupComponent)
    elif action == 'run_movecopy':
        movecopy.movecopy_from_csv_file(ui, title, fullLocationName, groupComponent)
    elif action == 'multiple_run_movecopy':
        movecopy.movecopy_from_csv_files(ui, title, fullLocationName, groupComponent)
    else:
        return False
    return True


def construct_assembly_from_csv_file(ui, title, assemblyFilename, hostComponent):
    """Construct assembly from CSV file, in hostComponent in Fusion360

    Input:
    . assemblyFilename: full path and name of assembly CSV file
    . hostComponent: place the assembly in the hostComponent
    Return: True when assembly component was constructed, else False

    Uses ui, title, assemblyFilename to report faults via Fusion360 GUI.
    """

    # Parse CSV file
    result, assemblyTuple = parse_csv_assembly_file(ui, title, assemblyFilename)
    if not result:
        return False
    assemblyComponentName, actions = assemblyTuple
    if len(actions) == 0:
        ui.messageBox('No valid actions in %s' % assemblyFilename, title)
        return False
    assemblyFolderName = os.path.dirname(assemblyFilename)

    # Create assembly component in hostComponent, if it does not already exist,
    # and make it the active component via isLightBulbOn
    assemblyComponent = utilities360.find_or_create_component(hostComponent,
                                                              assemblyComponentName, isLightBulbOn=True)
    interface360.print_text(ui, '> Assembly component: ' + assemblyComponent.name)

    # Construct assembly by processing the actions
    for actionTuple in actions:
        action, echoString, locationName, groupComponentName = actionTuple

        if action == 'echo':
            interface360.print_text(ui, 'Echo: ' + echoString)
            continue

        # Derive full location name of action CSV files folder or of single
        # action CSV file
        fullLocationName = os.path.join(assemblyFolderName, locationName)

        # Create group component for action result, if it does not already exist
        groupComponent = utilities360.find_or_create_component(assemblyComponent,
                                                               groupComponentName, isLightBulbOn=False)
        # Perform Fusion 360 command in groupComponent
        perform_action(ui, title, fullLocationName, groupComponent, action)
    interface360.print_text(ui, 'Created assembly for ' + assemblyFilename)
    return True


def construct_assemblies_from_csv_files(ui, title, folderName, hostComponent):
    """Construct assemblies from CSV files in folder, in hostComponent in
    Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: place the assemblies in the hostComponent
    Return: None

    Uses ui, title, folderName to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)
    if len(filenames) > 0:
        for filename in filenames:
            # Construct assembly from CSV file in hostComponent
            construct_assembly_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No assembly CSV files in %s' % folderName, title)
