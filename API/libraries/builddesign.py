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
# Date: 12 mar 2024
"""Module to build multiple assemblies from csv file into an toplevel
design component for a design in Fusion360.

Build design component for the different parts of an toplevel assembly
defined by a list of assembly CSV files. Each assembly CSV file defines a part
of the timeline actions in Fusion360. In order, the assembly CSV files
construct the entire timeline for the toplevel assembly in the design.

Design CSV file format:
. comment lines or comment in line will be removed
. first line: 'design' as filetype,
              filename of the design CSV file,
              name of the design component.
. next lines:
  - 'assembly_filenames' for list of assembly files
    . one assembly filename per line, the assembly filename is relative to
      folder of the design CSV file.

Remarks:
- If necessary build_design_from_csv_file() creates the
  designComponentName in the hostComponent. If the designComponentName
  is not specified, then use the activeComponent as designComponent.
"""

import os.path

import interfacefiles
import interface360
import utilities360
import constructassembly


def parse_csv_design_file(ui, title, filename):
    """Parse design CSV file.

    Reads script actions from an design CSV file filename.

    Input:
    . filename: full path and name of an design CSV file
    Return:
    . result: True when valid designTuple, else False with none
    . designTuple:
      - designComponentName: name of the design component

    Uses ui, title, filename to interact with user and report faults
    via Fusion360 GUI.
    """
    # Read design CSV file and remove comments and empty lines
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for design section and echo lines
    resultFalse = (False, None)
    assemblyFileNames = []
    echoLines = []
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'design':
                return resultFalse
            designFileName = lineArr[1]
            if designFileName not in filename:
                ui.messageBox('Filename %s in design CSV file does not match design CSV filename %s' %
                              (designFileName, filename), title)
                return resultFalse
            designComponentName = ''
            if len(lineArr) > 2:
                designComponentName = lineArr[2]
        else:
            # Read lists for:
            # . assembly_filenames
            # . echo lines
            if lineWord == 'assembly_filenames':
                pass
            elif lineWord == 'echo':
                echoLine = interfacefiles.convert_entries_to_single_string(lineArr[1:])
                echoLines.append(echoLine)
            else:
                assemblyFileNames.append(lineWord)
    if len(assemblyFileNames) == 0:
        ui.messageBox('No assembly files in %s' % filename, title)
        return resultFalse
    # Successfully reached end of file
    designTuple = (designFileName, designComponentName, assemblyFileNames, echoLines)
    return (True, designTuple)


def build_design_from_csv_file(ui, title, filename, hostComponent):
    """Build design from CSV file, in hostComponent in Fusion360

    Input:
    . filename: full path and name of design CSV file
    . hostComponent: place the design component in the hostComponent
    Return: True when design component was constructed, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """

    # Parse CSV file
    result, designTuple = parse_csv_design_file(ui, title, filename)
    if not result:
        return False
    designFileName, designComponentName, assemblyFileNames, echoLines = designTuple
    designFolderName = os.path.dirname(filename)

    # Create design component in hostComponent, if it does not already
    # exist, and make it visible via isLightBulbOn in create_component().
    designComponent = utilities360.find_or_create_component(hostComponent, designComponentName)
    interface360.print_text(ui, '> Design component: ' + designComponent.name)

    # Build design component by processing the assembly files
    for assemblyFileName in assemblyFileNames:
        assemblyFileName = os.path.join(designFolderName, assemblyFileName)
        constructassembly.construct_assembly_from_csv_file(ui, title, assemblyFileName, hostComponent)
    # Log echo lines
    for echoLine in echoLines:
        interface360.echo_text(ui, echoLine)
    interface360.print_text(ui, 'Built design for ' + filename)
    return True
