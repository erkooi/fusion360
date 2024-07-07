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
# Date: 2 feb 2024
"""Module to mirror body or component defined in a csv file into a new body or
   new component in Fusion360.

Mirror CSV file format:
. comment lines or comment in line will be removed
. first line: 'mirror' as filetype, name of the mirror file, name of the
  group component for the mirrored result.
. second line: 'mirror_plane', name of mirror plane
. third line: operation 'new_component', 'new_body', 'join'
  - For 'new_component' the object must be a component,
  - for 'new_body' or 'join' the object must be a body. Operation 'new_body'
    is opposite of operation 'join', so keep mirror results separate.
. mirror_objects
  - list of one or more object names, one per line.
  - The objects are all components or all bodies.
  - The original bodies are kept. For operation 'join' this is achieved by
    first copying the original bodies. For operation 'new_body' the original
    bodies are also copied and the list in mirror_results must contain
    names for first the mirrored bodies and then the copied original bodies.
. mirror_results
  - list of one or more result names, one per line.
  - The mirrored bodies get the names from resultObjectNames.
    . If operation is 'new_component' or 'new_body' then the resultObjectNames
      must have a name for each of the mirrored objects.
    . If operation is 'join' then typically there is only one result body and
      then resultObjectNames contains one name.

TODO:
  The mirror operation = 'new_component' is not (yet) supported. In
  mirrorFeatures.createInput(inputEntites, plane) the inputEntites can be an
  objectCollection of faces, features, bodies, or components, according to the
  manual, but for 'new_component' it does yield error 'inputEntities should be
  of a single type.'. Furthermore in the mirror result MirrorFeature object,
  there are bodies, faces and resultFeatures, but no field for components, so
  it is not clear how a mirrored component is represented.
"""

import adsk.fusion

import interfacefiles
import interface360
import utilities360


def parse_csv_mirror_file(ui, title, filename):
    """Parse mirror CSV file.

    Input:
    . filename: full path and name of CSV file
    Return:
    . result: True when valid mirrorTuple, else False with none
    . mirrorTuple:
      - operation: 'new_component', 'new_body' or 'join' body
      - planeName: name of mirror plane
      - mirrorObjectNames: list of object names to mirror
      - mirrorResultNames: list of names for the mirror results

    Uses ui, title, filename to interact with user and report faults via
    Fusion360 GUI.
    """
    # Read file and remove comment
    fileLines = interfacefiles.read_data_lines_from_file(filename)
    lineLists = interfacefiles.convert_data_lines_to_lists(fileLines)

    # Parse file lines for mirror
    resultFalse = (False, None)
    mirrorObjectNames = []
    mirrorResultNames = []
    readMirrorObjects = False
    readMirrorResults = False
    for li, lineArr in enumerate(lineLists):
        lineWord = lineArr[0]
        if li == 0:
            if lineWord != 'mirror':
                return resultFalse
            mirrorFilename = lineArr[1]
            groupComponentName = ''
            if len(lineArr) > 2:
                groupComponentName = lineArr[2]
        elif li == 1:
            # Read mirror operation
            if lineWord != 'operation':
                ui.messageBox('Expected mirror operation instead of %s in %s' % (lineWord, filename), title)
                return resultFalse
            operation = lineArr[1]
            if operation not in interfacefiles.validMirrorOperations:
                ui.messageBox('No valid mirror operation %s in %s' % (operation, filename), title)
                return resultFalse
        elif li == 2:
            # Read mirror plane
            if lineWord != 'mirror_plane':
                return resultFalse
            planeName = lineArr[1]
        else:
            # Read lists for:
            # . mirror_objects
            # . mirror_results
            if lineWord == 'mirror_objects':
                readMirrorObjects = True
                readMirrorResults = False
            elif lineWord == 'mirror_results':
                readMirrorObjects = False
                readMirrorResults = True
            else:
                if readMirrorObjects:
                    mirrorObjectNames.append(lineWord)
                elif readMirrorResults:
                    mirrorResultNames.append(lineWord)
    if len(mirrorObjectNames) == 0:
        ui.messageBox('Not enough mirror objects in %s' % filename, title)
        return resultFalse
    if len(mirrorResultNames) == 0:
        ui.messageBox('Not enough mirror results in %s' % filename, title)
        return resultFalse

    # Successfully reached end of file
    mirrorTuple = (mirrorFilename, groupComponentName, operation, planeName, mirrorObjectNames, mirrorResultNames)
    return (True, mirrorTuple)


def mirror_from_csv_file(ui, title, filename, hostComponent):
    """Mirror from CSV file, in hostComponent in Fusion360

    Input:
    . filename: full path and name of CSV file
    . hostComponent: with the mirror objects: component(s) or body, bodies
    Return:
    . True when mirror was created, else False

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    # Parse CSV file, mirrorFilename is not used
    result, mirrorTuple = parse_csv_mirror_file(ui, title, filename)
    if not result:
        return False
    _, groupComponentName, operation, planeName, mirrorObjectNames, mirrorResultNames = mirrorTuple

    # Find mirror plane in hostComponent Construction folder or in any sub
    # component
    mirrorPlane = utilities360.find_plane_anywhere(ui, hostComponent, planeName)
    if not mirrorPlane:
        interface360.error_text(ui, 'Mirror plane %s not found in %s' % (mirrorPlane, hostComponent.name))
        return False

    # Find mirror objects collection anywhere in hostComponent
    if operation == 'new_component':
        # find occurrences
        # . mirror operates on occurrences collection, not on components
        # . use rootComponent to avoid error: 'Compute Failed //
        #   NONROOT_OCCURRENCE_PATH_ROOT - Occurrence Path must be from root
        #   component'
        rootComponent = utilities360.get_root_component(hostComponent)
        result, mirrorObjects = utilities360.find_occurrences_collection_anywhere(ui, rootComponent, mirrorObjectNames)
    else:
        # find bodies
        result, mirrorObjects = utilities360.find_bodies_collection_anywhere(ui, hostComponent, mirrorObjectNames)
    if not result:
        interface360.error_text(ui, 'One or more mirror objects in %s not found' % str(mirrorObjectNames))
        return False

    # Mirror the object(s)
    if operation == 'new_component':
        result = mirror_occurrences(ui, hostComponent, mirrorPlane, mirrorObjects, mirrorResultNames)
    else:
        result, resultBodies = mirror_bodies(ui, hostComponent, operation,
                                             mirrorPlane, mirrorObjects, mirrorResultNames)

    # Move mirrored objects to the groupComponent, if the groupComponent is
    # another component then the parentComponent of the object.
    # . Create groupComponent in hostComponent for the mirrored objects, if
    #   it does not already exist, else use hostComponent if groupComponentName
    #   is empty string or is the hostComponent.
    # . Get parentComponent of the mirrored objects (component or body),
    #   because that is where the mirrored objects are.
    groupComponent = utilities360.find_or_create_component(hostComponent, groupComponentName)
    groupOccurrence = utilities360.get_occurrence_anywhere(groupComponent)
    if operation == 'new_component':
        pass
    else:
        for body in resultBodies:
            if groupComponent != body.parentComponent:
                utilities360.move_body_to_occurrence(body, groupOccurrence)

    if result:
        interface360.print_text(ui, 'Mirror for ' + filename)
    return result


def mirror_occurrences(ui, hostComponent, mirrorPlane, mirrorObjects, mirrorResultNames):
    """Mirror occurrences in plane and rename result occurrences.

    The mirror 'new_component' operation operates on an occurrences collection
    for mirror Feature.inputEntities, not on components. Uisng components
    collection yields error 'inputEntities should be of a single type.'

    Input:
    . hostComponent: with the occurrence(s) to mirror
    . mirrorPlane: mirror plane
    . mirrorObjects: objectCollection of occurrences to mirror in mirrorPlane
    . mirrorResultNames: list of names for the mirror results
    Return: True when mirror went OK, else False

    Uses ui to report faults via Fusion360 GUI.
    """
    # Prepare mirrorFeaturesInput
    mirrorFeatures = hostComponent.features.mirrorFeatures
    mirrorFeaturesInput = mirrorFeatures.createInput(mirrorObjects, mirrorPlane)

    # Perform the mirror feature
    # . No need to keep returned mirrorResult, because it does not contain
    #   information about the mirrored component
    mirrorFeatures.add(mirrorFeaturesInput)

    # Rename the result occurrences of the mirror
    result = _rename_result_occurrences(ui, hostComponent, mirrorObjects, mirrorResultNames)
    return result


def mirror_bodies(ui, hostComponent, operation, mirrorPlane, mirrorObjects, mirrorResultNames):
    """Mirror bodies in plane and rename result bodies.

    Copy bodies to keep original bodies in case of join operation.

    Input:
    . hostComponent: with the body or bodies to mirror
    . operation: 'new_body' or 'join' body
    . mirrorPlane: mirror plane
    . mirrorObjects: objectCollection of bodies to mirror in mirrorPlane
    . mirrorResultNames: list of names for the mirror results
    Return:
    . result: True when mirror went OK, else False
    . resultBodies: list of mirror result body objects

    Uses ui to report faults via Fusion360 GUI.
    """
    verbosity = False
    resultFalse = (False, None)
    # Use copy bodies:
    # . to keep original bodies in case of 'join' operation
    # . as work around for that mirrorFeatures.createInput() fails on input
    #   mirrorObjects ObjectCollection
    copyBodies = adsk.core.ObjectCollection.create()
    for body in mirrorObjects:
        # The body.parentComponent is unique in rootComponent.
        parentOccurrence = utilities360.get_occurrence_anywhere(body.parentComponent)
        copyBody = utilities360.copy_body_to_occurrence(body, parentOccurrence)
        copyBodies.add(copyBody)
        interface360.print_text(ui, 'body.name = %s' % body.name, verbosity)
        interface360.print_text(ui, 'body.parentComponent.name = %s' % body.parentComponent.name, verbosity)
        interface360.print_text(ui, 'copyBody.name = %s' % copyBody.name, verbosity)
    mirrorObjects = copyBodies
    interface360.print_text(ui, 'hostComponent.name = %s' % hostComponent.name, verbosity)

    # Prepare mirrorFeaturesInput
    mirrorFeatures = hostComponent.features.mirrorFeatures
    mirrorFeaturesInput = mirrorFeatures.createInput(mirrorObjects, mirrorPlane)
    if operation == 'join':
        mirrorFeaturesInput.isCombine = True
    interface360.print_text(ui, 'mirrorFeaturesInput.isCombine = %s' % str(mirrorFeaturesInput.isCombine), verbosity)

    # Perform the mirror feature
    mirrorResult = mirrorFeatures.add(mirrorFeaturesInput)

    # Rename the result oject or bodies of the mirror
    result, resultBodies = _rename_result_bodies(ui, mirrorResultNames, mirrorResult)
    if not result:
        interface360.error_text(ui, 'Rename result mirror bodies with %s failed' % str(mirrorResultNames))
        return resultFalse
    return (True, resultBodies)


def _rename_result_occurrences(ui, hostComponent, mirrorObjects, resultObjectNames):
    """Rename occurrences of mirror 'new_component' with names from
    resultObjectNames

    The mirror_bodies() uses mirrorResult of mirrorFeatures.add() to get access
    to the mirrored bodies. For mirror_occurrences the mirrored occurrences
    are not available via mirrorResult, therefor instead find the mirrored
    occurrences base on their default name. The 'new_component' occurrences
    default get the same name as the name of original mirrorObjects, but with
    '(Mirror)' as postfix. Each component in mirrorObjects gets mirrored, so
    resultObjectNames should contain the same amount of new names.

    Input:
    . hostComponent: with the mirrored occurrence(s), or use it to get the
      rootComponent in case the hostComponent itself is mirrored.
    . mirrorObjects: objectCollection of occurrences for mirror, used to
      derive named of mirrored occurrences
    . resultObjectNames: if list is empty, then keep default names, else use
      names from list to rename the new mirrored occurrences. If
      resultObjectNames contains not the same amount of names as the number of
      occurrences in mirrorResult, then report error via ui.
    Return: True when rename went OK, else False

    Uses ui to report faults via Fusion360 GUI.
    """
    nofMirrorObjects = len(mirrorObjects)
    nofResultObjectNames = len(resultObjectNames)
    if nofResultObjectNames > 0:
        if nofMirrorObjects == nofResultObjectNames:
            # Rename the mirrored components
            for mo in range(mirrorObjects.count):
                # Derive mirrored occurrence name from original occurrence name
                mirrorOccurrence = mirrorObjects.item(mo)
                mirrorComponent = mirrorOccurrence.component
                mirroredOccurrenceName = mirrorComponent.name + '(Mirror)'
                # Find component of mirrored occurrence.
                if hostComponent.name == mirrorComponent.name:
                    rootComponent = utilities360.get_root_component(hostComponent)
                    searchComponent = rootComponent
                else:
                    searchComponent = hostComponent
                mirroredComponent = utilities360.find_component_anywhere(searchComponent, mirroredOccurrenceName)
                # Rename the component to also rename its occurrence
                mirroredComponent.name = resultObjectNames[mo]
            return True
        else:
            # Report mismatch in number of mirrored components
            interface360.error_text(ui, 'nofMirrorObjects %d != %d nofResultObjectNames' %
                                    (nofMirrorObjects, nofResultObjectNames))
            return False
    else:
        # Keep default names for mirrored components
        return True


def _rename_result_bodies(ui, resultObjectNames, mirrorResult):
    """Rename bodies in mirrorResult with names from resultObjectNames

    Input:
    . resultObjectNames: if list is empty, then keep default names, else use
      names from list to rename the bodies in mirrorResult. If
      resultObjectNames contains not the same amount of names as the number of
      bodies in mirrorResult, then report error via ui.
    . mirrorResult: result feature of mirror.
    Return:
    . result: True when rename went OK, else False
    . resultBodies: list of mirror result body objects

    Uses ui to report faults via Fusion360 GUI.
    """
    resultFalse = (False, None)
    resultBodies = []
    nofResultObjectNames = len(resultObjectNames)
    if nofResultObjectNames > 0:
        if nofResultObjectNames == mirrorResult.bodies.count:
            # Rename the bodies of the mirror
            for oi in range(mirrorResult.bodies.count):
                body = mirrorResult.bodies.item(oi)
                body.name = resultObjectNames[oi]
                resultBodies.append(body)
            return (True, resultBodies)
        else:
            # Report actual mirror body names
            interface360.error_text(ui, 'mirror resultObjectNames = ' + str(resultObjectNames))
            interface360.error_text(ui, 'mirror nofResultObjectNames %d != %d mirrorResult.bodies.count' %
                                    (nofResultObjectNames, mirrorResult.bodies.count))
            for oi in range(mirrorResult.bodies.count):
                body = mirrorResult.bodies.item(oi)
                interface360.error_text(ui, 'mirror body.name = ' + str(body.name))
            return resultFalse
    else:
        # Keep default body names of the mirror
        for bi in range(mirrorResult.bodies.count):
            body = mirrorResult.bodies.item(bi)
            resultBodies.append(body)
        return (True, resultBodies)


def mirror_from_csv_files(ui, title, folderName, hostComponent):
    """Mirror from CSV files in folder, in hostComponent in Fusion360

    Input:
    . folderName: full path and folder name
    . hostComponent: with the mirror objects: component(s) or body, bodies
    Return: None

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    filenames = interfacefiles.get_list_of_files_in_folder(folderName)

    if len(filenames) > 0:
        for filename in filenames:
            # Mirror from CSV file in hostComponent
            mirror_from_csv_file(ui, title, filename, hostComponent)
    else:
        ui.messageBox('No mirror CSV files in %s' % folderName, title)
