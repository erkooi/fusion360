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
. first line: 'assembly' as filetype, name of the assembly component
. next lines: one assembly action per line, order of actions defines the design
  timeline. Valid actions are defined in interfacefiles.validAssemblyActions.
  Assembly actions can be done per csv directory or per csv file:
  . multiple_run_<action>, 'csv directory name', groupComponent
  . run_<action>, 'csv filename', groupComponentName

Remarks:
- If necessary create the assemblyComponent in the hostComponent
. Sketches and planes can be in seperate groupComponents within the
  assemblyComponent, because they do not rely other objects and can be found
  from the assemblyComponent. Therefor multiple_run_<action> can be used for
  action = sketch, plane.
. The groupComponent can be derived from the CSV sub directory name, or it can
  be specified explicitely in the assembly CSV file
. If an action depends on objects that are all in the same groupComponent,
  then the action can be done in that groupComponent as well. Therefor then
  the groupComponent can be derived from the CSV sub directory name
. If an action depends on objects that are in different groupComponents, then
  the action has to be done in their (parent) assemblyComponent. Therefor
  then specify the assemblyComponent as groupComponent for the action in the
  assembly CSV file.
- Object names have to be unique in whole assembly, so they can be referred
  to from anywhere in the assembly component without having to specify
  where they are located.
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


def parse_csv_assembly_file(ui, title, filename):
    """Parse assembly CSV file.

    Reads script actions from an assembly CSV file filename.

    Input:
    . filename: full path and name of an assembly CSV file
    Return:
    . result: True when valid assemblyTuple, else False with none
    . assemblyTuple:
      - assemblyComponentName: name of the assembly component
      - actions: list of actionTuples
        . actionTuple:
          - action: assembly action from interfacefiles.validAssemblyActions.
          - locationName: sub directory name of action CSV files or sub.
            directory name plus filename of one action CSV file. The
            locationName directory is relative to the directory of filename.
          - groupComponentName: Optional group component name for action
            results. Default extract group component name from locationName.

    Uses ui, title, filename to interact with user and report faults
    via Fusion360 GUI.
    """
    # Read assembly CSV file and remove comments and empty lines
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for assembly sections
    resultFalse = (False, None)
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'assembly':
                return resultFalse
            assemblyComponentName = lineArr[1]
            actions = []
        else:
            # Read assembly actions, one per line
            if lineWord not in interfacefiles.validAssemblyActions:
                ui.messageBox('Not a valid action %s in %s' % (lineWord, filename), title)
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
                    ui.messageBox('Cannot extract or read group component name from %s' % filename, title)
            actionTuple = (action, echoString, locationName, groupComponentName)
            actions.append(actionTuple)
    if len(actions) == 0:
        ui.messageBox('No actions in %s' % filename, title)
        return resultFalse
    # Successfully reached end of file
    assemblyTuple = (assemblyComponentName, actions)
    return (True, assemblyTuple)


def perform_action(ui, title, locationName, groupComponent, action):
    """Perform action in groupComponent

    Input:
    . action: Fusion 360 command, specified in CSV file
    . locationName: full location name for CSV directory or file
    . groupComponent: group component name for action results

    Return: True when action is done, else False
    """
    # . Sketches and planes can be in seperate group components within the
    #   hostComponent.
    if action == 'create_sketch':
        importsketch.create_sketch_from_csv_file(ui, title, locationName, groupComponent)
    elif action == 'multiple_create_sketch':
        importsketch.create_sketches_from_csv_files(ui, title, locationName, groupComponent)
    elif action == 'create_plane':
        createplane.create_plane_from_csv_file(ui, title, locationName, groupComponent)
    elif action == 'multiple_create_plane':
        createplane.create_planes_from_csv_files(ui, title, locationName, groupComponent)

    # . Bodies need to be in the groupComponent = hostComponent, because
    #   they build upon on sketches, planes and bodies.
    elif action == 'run_extrude':
        extrude.extrude_from_csv_file(ui, title, locationName, groupComponent)
    elif action == 'multiple_run_extrude':
        extrude.extrudes_from_csv_files(ui, title, locationName, groupComponent)
    elif action == 'create_loft':
        createloft.create_loft_from_csv_file(ui, title, locationName, groupComponent)
    elif action == 'multiple_create_loft':
        createloft.create_lofts_from_csv_files(ui, title, locationName, groupComponent)
    elif action == 'run_combine':
        combinebodies.combine_bodies_from_csv_file(ui, title, locationName, groupComponent)
    elif action == 'multiple_run_combine':
        combinebodies.combine_bodies_from_csv_files(ui, title, locationName, groupComponent)
    elif action == 'run_split':
        splitbody.split_body_from_csv_file(ui, title, locationName, groupComponent)
    elif action == 'multiple_run_split':
        splitbody.split_bodies_from_csv_files(ui, title, locationName, groupComponent)
    elif action == 'run_movecopy':
        movecopy.movecopy_from_csv_file(ui, title, locationName, groupComponent)
    elif action == 'multiple_run_movecopy':
        movecopy.movecopy_from_csv_files(ui, title, locationName, groupComponent)
    else:
        return False
    return True


def construct_assembly_from_csv_file(ui, title, filename, hostComponent):
    """Construct assembly from CSV file, in hostComponent in Fusion360

    Input:
    . filename: full path and name of assembly CSV file
    . hostComponent: place the assembly in the hostComponent
    Return: True when assembly component was constructed, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """

    # Parse CSV file
    result, assemblyTuple = parse_csv_assembly_file(ui, title, filename)
    if not result:
        return False
    assemblyComponentName, actions = assemblyTuple
    if len(actions) == 0:
        ui.messageBox('No valid actions in %s' % filename, title)
        return False
    assemblyFolderName = os.path.dirname(filename)

    # Create assembly component in hostComponent, if it does not already exist,
    # and make it visible via isLightBulbOn
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
        locationName = os.path.join(assemblyFolderName, locationName)
        locationName = os.path.normpath(locationName)

        # Create group component for action result, if it does not already exist
        groupComponent = utilities360.find_or_create_component(assemblyComponent,
                                                               groupComponentName, isLightBulbOn=False)
        # Perform Fusion 360 command in groupComponent
        perform_action(ui, title, locationName, groupComponent, action)
    interface360.print_text(ui, 'Created assembly for ' + filename)
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
