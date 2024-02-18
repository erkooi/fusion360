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
# Date: 11 feb 2024
"""Module with example samples for using the API in Fusion360.
"""

import adsk.core


def create_example_objects(component):
    """Create some objects in Fusion360, like sketch, body, face, plane, mirror

    Purpose is to show how these objects can be created and to get access to
    their properties.

    Based on code in 'Mirror Feature API Sample' at:
      https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-81e2da74-eee7-11e4-86e4-f8b156d7cd97

    Input:
    . component: place the objects in component.
    Return: objectsTuple with properties and items
    . sketchTuple
    . extrudeTuple
    . planeTuple
    . mirrorTuple
    """
    # Create sketch
    sketches = component.sketches
    sketch = sketches.add(component.xZConstructionPlane)
    sketchLines = sketch.sketchCurves.sketchLines
    startPoint = adsk.core.Point3D.create(0, 0, 0)
    endPoint = adsk.core.Point3D.create(5, 5, 0)
    sketchLines.addTwoPointRectangle(startPoint, endPoint)

    # Get the profile defined by the rectangle.
    profile = sketch.profiles.item(0)

    # Create an extrusion input.
    features = component.features
    extrudeFeatures = features.extrudeFeatures
    extrudeFeaturesInput = extrudeFeatures.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

    # Define that the extent is a distance extent of 5 cm.
    distance = adsk.core.ValueInput.createByReal(5)
    extrudeFeaturesInput.setDistanceExtent(False, distance)

    # Create the extrusion.
    extrudeResult = extrudeFeatures.add(extrudeFeaturesInput)

    # Get the body created by extrusion
    extrudeBody = extrudeResult.bodies.item(0)

    # Get a face of the body
    extrudeFace = extrudeBody.faces.item(0)

    # Create a construction plane by offset
    planes = component.constructionPlanes
    planeInput = planes.createInput()
    offsetDistance = adsk.core.ValueInput.createByString('5 cm')
    planeInput.setByOffset(extrudeFace, offsetDistance)
    planeResult = planes.add(planeInput)

    # Create input entities for mirror feature
    inputEntites = adsk.core.ObjectCollection.create()
    inputEntites.add(extrudeBody)

    # Create the input for mirror feature
    mirrorFeatures = features.mirrorFeatures
    mirrorInput = mirrorFeatures.createInput(inputEntites, planeResult)

    # Create the mirror feature
    mirrorResult = mirrorFeatures.add(mirrorInput)

    # Return objects in tuples
    sketchTuple = (sketch, profile)
    extrudeTuple = (extrudeFeaturesInput, extrudeResult, extrudeBody, extrudeFace)
    planeTuple = (planeInput, planeResult)
    mirrorTuple = (mirrorInput, mirrorResult)

    objectsTuple = (sketchTuple, extrudeTuple, planeTuple, mirrorTuple)
    return objectsTuple


def traverseAssembly(occurrences, currentLevel, inputString):
    """Assembly traversal using recursion to print names of all occurrences.

    Recursive function that traverses the entire hierarchy of the currently
    open assembly to find and print all occurrences.

    Based on code in 'Assembly traversal using recursion API Sample' at:
        https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-5a4fa3a6-fa21-11e4-b610-f8b156d7cd97

    Input:
    . occurrences: start with rootComp.occurrences.asList
    . currentLevel: start at currentLevel = 1
    . inputString: input string with found occurrences till currentLevel
    Return:
    . inputString: updated string with found occurrences till currentLevel
    """
    indent = ' ' * 4
    for i in range(0, occurrences.count):
        occ = occurrences.item(i)
        inputString += indent * currentLevel + occ.name + '\n'
        if occ.childOccurrences:
            inputString = traverseAssembly(occ.childOccurrences, currentLevel + 1, inputString)
    return inputString
