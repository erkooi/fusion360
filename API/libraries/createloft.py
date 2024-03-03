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
# Date: 7 may 2023
"""Module to create a loft from sketch profiles and rails defined in a csv file
   into a component in Fusion360.

The profile can be a sketch profile or a sketch point. The profile index is 0
if there is only one profile:
. If there are multiple sketch profiles, then manually find the index using the
  Fusion360 GUI.
. If the profile is a sketch point, then then the origin has index 0, so the
  first user sketch point has index 1.

Loft CSV file format:
. comment lines or comment in line will be removed
. first line: 'loft' as filetype, name of the loft, name of the group
  component for the loft.
. profiles
  - sketch name, optional item index  # one per line
. rails
  - sketch name, optional item index  # one per line

Remark:
. Loft between profiles with a hole does still create a fully filled body, so
  the hole in the profile is ignored.
"""

import adsk.fusion

import interfacefiles
import interface360
import utilities360

validLoftSketches = ['profiles', 'rails']


def parse_csv_loft_file(ui, title, filename):
    """Parse loft CSV file.

    Reads loft name and sketch names for profiles and rails from csv file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid loftTuple, else False with None
    . loftTuple:
      - loftName: name for loft object
      - groupComponentName: group component for the loft object
      - profileTuples: list of profile sketches (sketch name, profile item
        index)
      - railTuples: list of rail sketches (sketch name, rail item index)

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for loft
    resultFalse = (False, None)
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'loft':
                return resultFalse
            loftName = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
            profileTuples = []
            railTuples = []
            addProfiles = False
            addRails = False
        else:
            # Read sketch names for profiles and rails
            if lineWord == 'profiles':
                addProfiles = True
                addRails = False
            elif lineWord == 'rails':
                addProfiles = False
                addRails = True
            else:
                itemIndex = 0
                if len(lineArr) > 1:
                    itemIndex = int(lineArr[1])
                if addProfiles:
                    profileTuples.append((lineWord, itemIndex))
                if addRails:
                    railTuples.append((lineWord, itemIndex))

    if len(profileTuples) < 2:
        ui.messageBox('Not enough profiles for loft in %s' % filename, title)
        return resultFalse

    # Successfully reached end of file
    loftTuple = (loftName, groupComponentName, profileTuples, railTuples)
    return (True, loftTuple)


def create_loft_from_csv_file(ui, title, filename, hostComponent, loftNewComponent=False):
    """Create loft from CSV file, in Fusion360

    Dependent on the groupComponentName the loft object will be put in the
    hostComponent or in the hostComponent/groupComponent.
    Dependent on loftNewComponent the loft will be put in the Bodies
    folder or in the Bodies folder of a new loft component.

    The sketches for the profiles and rails are searched for anywhere in the
    hostComponent.

    Input:
    . filename: full path and name of CSV file
    . hostComponent: host component for the loft
    . loftNewComponent: when True create loft component, else create loft body
    Return:
    . True when loft was created, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    verbosity = False  # no print_text()

    # Parse CSV file
    result, loftTuple = parse_csv_loft_file(ui, title, filename)
    if not result:
        return False
    loftName, groupComponentName, profileTuples, railTuples = loftTuple

    interface360.print_text(ui, 'profileTuples: %s' % profileTuples, verbosity)
    interface360.print_text(ui, 'railTuples   : %s' % railTuples, verbosity)

    # Find profiles in sketches anywhere in hostComponent
    profiles = []
    for pt in profileTuples:
        name = pt[0]
        index = pt[1]
        sketch = utilities360.find_sketch_anywhere(ui, hostComponent, name)
        if sketch:
            if index < sketch.profiles.count:
                # Loft profile is a sketch profile
                interface360.print_text(ui, name + ': %d profiles' % sketch.profiles.count, verbosity)
                profiles.append((name, sketch.profiles.item(index)))
            elif index < sketch.sketchPoints.count:
                # Loft profile is a sketch point
                interface360.print_text(ui, name + ': %d points' % sketch.sketchPoints.count, verbosity)
                profiles.append((name, sketch.sketchPoints.item(index)))
            else:
                interface360.error_text(ui, 'Sketch %s has no profile or point index %d' % (name, index))
                return False
        else:
            interface360.error_text(ui, 'Profile sketch %s not found' % name)
            return False

    # Find rails in sketches anywhere in hostComponent
    rails = []
    for rt in railTuples:
        name = rt[0]
        index = rt[1]
        sketch = utilities360.find_sketch_anywhere(ui, hostComponent, name)
        if sketch:
            interface360.print_text(ui, sketch.name + ': %d curves' % sketch.sketchCurves.count, verbosity)
            if index < sketch.sketchCurves.count:
                rails.append((name, sketch.sketchCurves.item(index)))
            else:
                interface360.error_text(ui, 'Sketch %s has no rail index %d' % (name, index))
                return False
        else:
            interface360.error_text(ui, 'Rail sketch %s not found' % name)
            return False

    # Create groupComponent in hostComponent for loft object, if it does not
    # already exist, else use hostComponent if groupComponentName is empty
    # string or is the hostComponent.
    groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)

    # Create loft feature input in groupComponent
    loftFeatures = groupComponent.features.loftFeatures
    if loftNewComponent:
        loftFeatureInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewComponentFeatureOperation)
    else:
        loftFeatureInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    for profile in profiles:
        # profile = (name, object)
        if not loftFeatureInput.loftSections.add(profile[1]):
            interface360.error_text(ui, 'Profile %s not added' % profile[0])
            return False
    for rail in rails:
        # rail = (name, object)
        if not loftFeatureInput.centerLineOrRails.addRail(rail[1]):
            interface360.error_text(ui, 'Rail %s not added' % rail[0])
            return False
    loftFeatureInput.isSolid = True
    loftFeatureInput.isClosed = False
    loftFeatureInput.isTangentEdgesMerged = True

    # Create loft feature
    loftFeature = loftFeatures.add(loftFeatureInput)

    # Rename loft result
    if loftNewComponent:
        loftFeature.parentComponent.name = loftName
    else:
        # loftFeature.name --> 'Loft1', 'Loft2', etc
        bodies = loftFeature.bodies
        body = bodies.item(0)
        body.name = loftName
        interface360.print_text(ui, 'body name: ' + body.name, verbosity)
    interface360.print_text(ui, 'Created loft for ' + filename)
    return True


def create_lofts_from_csv_files(ui, title, folderName, hostComponent, loftNewComponents=False):
    """Create lofts from CSV files in folder, in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: host component for the lofts
    . loftNewComponents: when True create loft components, else create loft
      bodies
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Create loft from CSV file in hostComponent
            create_loft_from_csv_file(ui, title, filename, hostComponent, loftNewComponents)
    else:
        ui.messageBox('No loft CSV files in %s' % folderName, title)
