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
# Date: 1 jun 2023
"""Module with utilities to create and modify objects in a design in Fusion360.
"""

import adsk.core

import interface360


################################################################################
# Find object

def find_sketch_anywhere(hostComponent, sketchName):
    """Find (first) sketch with sketchName anywhere in hostComponent.

    Input:
    . hostComponent: component object to search through.
    . sketchName: sketch name to search for
    Return:
    . sketch: sketch object when found, else None
    """
    # First look in hostComponent sketches
    sketches = hostComponent.sketches
    for s in range(0, sketches.count):
        sketch = sketches.item(s)
        if sketch.name == sketchName:
            return sketch  # Found sketch
    # Then search further in all occurrences
    occurrenceList = hostComponent.allOccurrences
    for i in range(0, occurrenceList.count):
        occurrence = occurrenceList.item(i)
        sketches = occurrence.component.sketches
        for s in range(0, sketches.count):
            sketch = sketches.item(s)
            if sketch.name == sketchName:
                return sketch  # Found sketch
    # Sketch not found
    return None


def find_profiles_collection(ui, sketch, profileIndices):
    """Find collection profiles with profileIndices in sketch

    Input:
    . sketch: sketch object
    . profileIndices: one or more indices of profiles in sketch
    Return:
    . profiles: profiles object collection for profileIndices in sketch, else
        None

    Uses ui to report faults via Fusion360 GUI.
    """
    profiles = adsk.core.ObjectCollection.create()
    for profileIndex in profileIndices:
        if profileIndex < sketch.profiles.count:
            profile = sketch.profiles.item(profileIndex)
            profiles.add(profile)
        else:
            interface360.error_text(ui, 'Sketch %s has no profile index %d' % (sketch.name, profileIndex))
            return None
    return profiles


def find_faces_collection(ui, body, faceIndices):
    """Find collection faces with faceIndices in body

    Input:
    . body: body object
    . faceIndices: one or more indices of faces in body
    Return:
    . faces: faces object collection for faceIndices in body, else None

    Uses ui to report faults via Fusion360 GUI.
    """
    faces = adsk.core.ObjectCollection.create()
    for faceIndex in faceIndices:
        if faceIndex < body.faces.count:
            face = body.faces.item(faceIndex)
            faces.add(face)
        else:
            interface360.error_text(ui, 'Body %s has no face index %d' % (body.name, faceIndex))
            return None
    return faces


def find_plane_anywhere(ui, hostComponent, planeName):
    """Find (first) plane with planeName anywhere in hostComponent.

    The planeName can be of a custom plane, or the name of one of the three
    construction planes through the origin of the rootComponent:

    . rootXyConstructionPlane
    . rootXzConstructionPlane
    . rootYzConstructionPlane

    or an origin plane through the origin of the hostComponent:

    . xYConstructionPlane
    . xZConstructionPlane
    . yZConstructionPlane

    Input:
    . hostComponent: component object to search through.
    . planeName: plane name to search for
    Return:
    . plane: plane object when found, else None
    """
    # First check whether planeName is an origin construction plane in the
    # rootComponent, return if found plane
    rootComponent = get_root_component(hostComponent)
    if planeName == 'rootXyConstructionPlane':
        return rootComponent.xYConstructionPlane
    if planeName == 'rootXzConstructionPlane':
        return rootComponent.xZConstructionPlane
    if planeName == 'rootYzConstructionPlane':
        return rootComponent.yZConstructionPlane

    # Then look in hostComponent, return if found plane
    if planeName == 'xYConstructionPlane':
        return hostComponent.xYConstructionPlane
    if planeName == 'xZConstructionPlane':
        return hostComponent.xZConstructionPlane
    if planeName == 'yZConstructionPlane':
        return hostComponent.yZConstructionPlane

    # Then look in hostComponent constructionPlanes
    constructionPlanes = hostComponent.constructionPlanes
    for s in range(0, constructionPlanes.count):
        plane = constructionPlanes.item(s)
        if plane.name == planeName:
            return plane  # Found plane

    # Then search further in constructionPlanes of all occurrences
    occurrenceList = hostComponent.allOccurrences
    for i in range(0, occurrenceList.count):
        occurrence = occurrenceList.item(i)
        constructionPlanes = occurrence.component.constructionPlanes
        for s in range(0, constructionPlanes.count):
            plane = constructionPlanes.item(s)
            if plane.name == planeName:
                return plane  # Found plane
    # Plane not found
    return None


def find_body(hostComponent, bodyName):
    """Find body with bodyName in this hostComponent.

    Input:
    . hostComponent: component object to search through.
    . bodyName: body name to look for
    Return:
    . body: body object when found, else None
    """
    return hostComponent.bRepBodies.itemByName(bodyName)


def find_body_anywhere(hostComponent, bodyName):
    """Find (first) body with bodyName anywhere in hostComponent.

    Input:
    . hostComponent: component object to search through, first look in bodies,
      then search in all occurrences.
    . bodyName: body name to search for
    Return:
    . body: body object when found, else None
    """
    # First look in hostComponent bodies
    body = find_body(hostComponent, bodyName)
    if body:
        return body
    # Then search further in all occurrences
    occurrenceList = hostComponent.allOccurrences
    for i in range(0, occurrenceList.count):
        occurrence = occurrenceList.item(i)
        bRepBodies = occurrence.component.bRepBodies
        for s in range(0, bRepBodies.count):
            body = bRepBodies.item(s)
            if body.name == bodyName:
                return body  # Found body
    # Body not found
    return None


def find_bodies_collection_anywhere(ui, hostComponent, bodyNames):
    """Find collection of bodies that match the bodyNames, anywhere in
    hostComponent.

    Input:
    . hostComponent: host component to search in for the bodies.
    . bodyNames: body names to look for
    Return:
    . result: True when all bodyNames were found, else False
    . bodies: ObjectCollection with found bodies

    Uses ui to report faults via Fusion360 GUI.
    """
    result = True
    bodies = adsk.core.ObjectCollection.create()
    for bodyName in bodyNames:
        body = find_body_anywhere(hostComponent, bodyName)
        if body:
            bodies.add(body)
        else:
            interface360.error_text(ui, 'Body %s not found in component %s' % (bodyName, hostComponent.name))
            result = False
    return (result, bodies)


def find_occurrences_anywhere(hostComponent, componentName):
    """Find occurrence(s) with componentName anywhere in hostComponent.

    . If the hostComponent itself has componentName, then
      - if hostComponent is the rootComponent return the rootComponent as
         single occurrence
      - else return occurrences of hostComponent anywhere in rootComponent.
    . else return occurrences of componentName anywhere in hostComponent.

    Component and occurrence:
      An occurrence is like an instance of a component. There can be one or
      more occurrences of a component. The place in design hierarchy of a new
      component also is its first occurrence. For the root component there is
      no occurrence, because there can only be one root component.
      . The root component can not be moved or copied.
      . For example in BRepBody.copyToComponent(target) the target can be
        either the root component or an occurrence. Therefore if component is
        the root component and the root component has componentName, then
        return the root component as occurrence.

    Input:
    . hostComponent: host component to search in for the component.
    . componentName: occurrence name to search for
    Return:
    . occurrences: list of found occurrence objects or the rootComponent
    """
    occurrences = []
    rootComponent = get_root_component(hostComponent)
    if hostComponent.name == componentName:
        if hostComponent == rootComponent:
            # If the rootComponent is the hostComponent and has componentName,
            # then return rootComponent as single occurrence
            occurrences.append(rootComponent)
            return occurrences
        else:
            searchComponent = rootComponent
    else:
        searchComponent = hostComponent

    # If hostComponent has componentName, then search in rootComponent for
    # occurrences of the componentName, else search in hostComponent
    occurrenceList = searchComponent.allOccurrences
    for i in range(0, occurrenceList.count):
        occurrence = occurrenceList.item(i)
        if componentName == occurrence.component.name:
            # Found occurrence with componentName
            occurrences.append(occurrence)
    return occurrences


def get_last_occurrence_anywhere(component, hostComponent=None):
    """Get last occurrence of component anywhere.

    If hostComponent is None then search anywhere in design hierarchy, else
    only search anywhere in hostComponent.

    The last occurrence is the newest occurrence or the only occurrence.

    Input:
    . component: component object
    . hostComponent: host component to search in for the component. If
      hostComponent is None, then search in the rootComponent.
    Return:
    . lastOccurrence: last occurrence of component in design hierarchy
    """
    if hostComponent is None:
        hostComponent = get_root_component(component)
    componentOccurrences = find_occurrences_anywhere(hostComponent, component.name)
    lastOccurrence = componentOccurrences[-1]
    return lastOccurrence


def find_component_anywhere(hostComponent, componentName):
    """Find component with componentName anywhere in hostComponent.

    . If componentName is name of hostComponent then return hostComponent.
    . If componentName is not name of hostComponent then return component
      within hostComponent.

    Input:
    . hostComponent: host component to search in for the component.
    . componentName: name of the component to search for
    Return:
    . None if the component with componentName is not found, else
      component object of the component with componentName in hostComponent,
      or the hostComponent itself if it has componentName.
    """
    # Look for componentName in hostComponent
    occurrences = find_occurrences_anywhere(hostComponent, componentName)
    if len(occurrences) == 0:
        # No occurrence of componentName found
        return None
    else:
        # Found occurrence of componentName in hostComponent
        occurrence = occurrences[0]
        component = occurrence.component
    return component


def find_components_collection_anywhere(ui, hostComponent, componentNames):
    """Find collection of components that match the componentNames, anywhere in
    hostComponent.

    Input:
    . hostComponent: search for components in hostComponent.
    . componentNames: component names to look for
    Return:
    . result: True when all componentNames were found, else False
    . components: ObjectCollection with found components

    Uses ui to report faults via Fusion360 GUI.
    """
    result = True
    components = adsk.core.ObjectCollection.create()
    for componentName in componentNames:
        component = find_component_anywhere(hostComponent, componentName)
        if component:
            components.add(component)
        else:
            interface360.error_text(ui, 'Component %s not found in component %s' % (componentName, hostComponent.name))
            result = False
    return (result, components)


def find_occurrences_collection_anywhere(ui, hostComponent, componentNames):
    """Find collection of occurrences that match the componentNames, anywhere
    in hostComponent.

    Input:
    . hostComponent: search for occurrences in hostComponent.
    . componentNames: occurrence names to look for
    Return:
    . result: True when all componentNames were found, else False
    . occurrences: ObjectCollection with found occurrences

    Uses ui to report faults via Fusion360 GUI.
    """
    result = True
    occurrences = adsk.core.ObjectCollection.create()
    for componentName in componentNames:
        component = find_component_anywhere(hostComponent, componentName)
        occurrence = get_last_occurrence_anywhere(component, hostComponent)
        if occurrence:
            occurrences.add(occurrence)
        else:
            interface360.error_text(ui, 'Occurrence %s not found in component %s' % (componentName, hostComponent.name))
            result = False
    return (result, occurrences)


def get_root_component(component):
    """Get rootComponent of component in design hierarchy

    Input:
    . component: component object
    Return:
    . rootComponent: root component in design hierarchy
    """
    rootComponent = component.parentDesign.rootComponent
    return rootComponent


def get_feature_operation_enum(operation):
    """Get adsk enum value for feature operation name.

    Input:
    . operation: feature operation name
    Return:
    . adsk enum for operation name else None when operation name is unknown
    """
    if operation == 'join':
        return adsk.fusion.FeatureOperations.JoinFeatureOperation
    if operation == 'cut':
        return adsk.fusion.FeatureOperations.CutFeatureOperation
    if operation == 'intersect':
        return adsk.fusion.FeatureOperations.IntersectFeatureOperation
    if operation == 'new_body':
        return adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    if operation == 'new_component':
        return adsk.fusion.FeatureOperations.NewComponentFeatureOperation
    return None


################################################################################
# Create object

def create_example_objects(component):
    """Create some objects in Fusion360, like sketch, body, face, plane, mirror

    Purpose is to show how these objects can be created and to get access to
    their properties.

    Based on code in Mirror Feature API Sample at:
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


def create_sketch_in_plane(hostComponent, sketchName, plane):
    """Create sketch in plane.

    Input:
    . hostComponent: place the sketch in hostComponent.
    . sketchName: name for the sketch
    . plane: plane object
    Return:
    . sketch: sketch object
    """
    # Create sketch in plane
    sketch = hostComponent.sketches.add(plane)
    sketch.name = sketchName
    return sketch


def create_transform_matrix3D(ui, operation, vector3D, angle=0.0):
    """Create transform Matrix3D for transform operation.

    Input:
    . operation: transform operation in validTransformOperations
    . vector3D: translation vector or rotation axis vector
    . angle: rotation angle in radians
    Return:
    . Matrix3D for transform operation when ok, else None.

    Uses ui to report faults via Fusion360 GUI.
    """
    transform = adsk.core.Matrix3D.create()
    if operation == 'translate':
        transform.translation = vector3D
    elif operation == 'rotate':
        origin3D = adsk.core.Point3D.create(0, 0, 0)
        transform.setToRotation(angle, vector3D, origin3D)
    else:
        interface360.error_text(ui, 'Unknown transform operation %s' % operation)
        return None
    return transform


def create_component(hostComponent, componentName):
    """Create new component with componentName in hostComponent.

    Default put isLightBulbOn of new component occurrence on.

    Input:
    . hostComponent: host component for the new component
    . componentName: name for new component
    Return:
    . component object of the new component
    """
    transform = adsk.core.Matrix3D.create()  # identity matrix
    occurrence = hostComponent.occurrences.addNewComponent(transform)
    occurrence.isLightBulbOn = True
    occurrence.component.name = componentName
    return occurrence.component


def find_or_create_component(hostComponent, componentName):
    """Find component with componentName in hostComponent or else create
       component with componentName in hostComponent. If componentName is
       name of hostComponent then return hostComponent.

    Default put isLightBulbOn of new component occurrence on in
    create_component().

    Input:
    . hostComponent: host component to search for the component
    . componentName: name for the component
    Return:
    . component object of the component with componentName in hostComponent,
      or the hostComponent itself if it has componentName.
    """
    # Check whether hostComponent has componentName, or look for componentName
    # in hostComponent
    component = find_component_anywhere(hostComponent, componentName)
    if component is None:
        # Create new component in hostComponent
        component = create_component(hostComponent, componentName)
    # else: Found occurrence of componentName in hostComponent
    return component


################################################################################
# Copy, move object in design hierarchy

def move_occurrence_to_occurrence(occurrence, targetOccurrence):
    """Move occurrence to targetOccurrence.

    Moves this occurrence from it's current component into the component owned
    by the targetOccurrence.

    Input:
    . occurrence: Occurrence object to copy
    . targetOccurrence: move occurrence to targetOccurrence
    Return:
    . movedOccurrence: Occurrence object of moved occurrence
    """
    movedOccurrence = occurrence.moveToComponent(targetOccurrence)
    return movedOccurrence


def copy_component_to_occurrence(component, targetOccurrence):
    """Copy component as new to targetOccurrence.

    First copy in rootComponent, because RuntimeError for addNewComponentCopy
    says 'transform overrides can only be set on Occurrence proxy from root
    component'. Then move to targetOccurrence, if the targetOccurrence in not
    already the rootComponent.

    Input:
    . component: component object to copy
    . targetOccurrence: copy component as new to targetOccurrence
    Return:
    . copiedComponent: component object of copied component
    """
    transform = adsk.core.Matrix3D.create()  # identity matrix
    # First copy component as new in rootComponent
    rootComponent = get_root_component(component)
    newCopyOccurrence = rootComponent.occurrences.addNewComponentCopy(component, transform)
    # Then move occurrence of new component to targetOccurrence
    if targetOccurrence != rootComponent:
        newCopyOccurrence = move_occurrence_to_occurrence(newCopyOccurrence, targetOccurrence)
    return newCopyOccurrence


def copy_body_to_occurrence(body, target):
    """Copy body to target.

    Input:
    . body: BRepBody object to copy
    . target: copy body to bodies in target, target can be either the root
      component or an occurrence
    Return:
    . copiedBody: BRepBody object of copied body
    """
    copiedBody = body.copyToComponent(target)
    return copiedBody


def move_body_to_occurrence(body, target):
    """Move body to target.

    Input:
    . body: BRepBody object to copy
    . target: move body to bodies in target, target can be either the root
      component or an occurrence
    Return:
    . movedBody: BRepBody object of moved body
    """
    movedBody = body.moveToComponent(target)
    return movedBody


def remove_bodies_anywhere(ui, hostComponent, bodyNames):
    """Remove bodies from anywhere in hostComponent.

    Input:
    . hostComponent: host component where the bodies are searched in
    . bodyNames: list of names of bodies to remove from hostComponent
    Return: True when bodies were removed, else false

    Uses ui to report faults via Fusion360 GUI.
    """
    if len(bodyNames) > 0:
        for bodyName in bodyNames:
            body = find_body_anywhere(hostComponent, bodyName)
            if body:
                # Must use removeFeatures from parentComponent of body, this
                # can be hostComponent, but may also be a sub component within
                # hostComponent.
                removeFeatures = body.parentComponent.features.removeFeatures
                removeFeatures.add(body)
            else:
                interface360.error_text(ui, 'Remove body %s not found in %s' % (bodyName, hostComponent.name))
                return False


################################################################################
# Transform object in design 3d space

def transform_occurrence(ui, occurrence, transformTuple):
    """Transform occurrence in Fusion360

    Mechanisms:
    a)The moveFeatures.createInput2() appears to not support transform of a
      objectCollection with component or occurrence.
    b)With occurrence.transform2() = transform only the last transform in a
      series determines the orientation and position of the occurrence, so
      intermediate transforms are not captured.
    c)The rootComponent.transformOccurrences() is for faster transform of list
      of occurrences in a design.
    Mechanisms b) and c ) appear equivalent.

    TODO: Using design.snapshots.add() does capture the position in timeline,
          but next transform still does not continue from there.

    Input:
    . occurrence: occurrence object to transform
    . transformTuple:
      - transformOperation: 'translate' or 'rotate'
      - vector3D: translation vector or rotation axis vector
      - angle: rotation angle in radians
    Return:
    . None

    Uses ui to report faults via Fusion360 GUI.
    """
    transformOperation, vector3D, angle = transformTuple
    interface360.print_text(ui, '%s, vector %f, %f, %f, angle %f' %
                            (transformOperation, vector3D.x, vector3D.y, vector3D.z, angle))
    # Create a transform
    transform = create_transform_matrix3D(ui, transformOperation, vector3D, angle)
    # Do the transform, both mechanisms are equivalent
    rootComponent = get_root_component(occurrence.component)
    if True:
        occurrence.transform2 = transform
    else:
        rootComponent.transformOccurrences([occurrence], [transform], ignoreJoints=True)
    # Capture position using snapshots.add(), snapshots.hasPendingSnapshot is
    # True because of transform.
    rootComponent.parentDesign.snapshots.add()


def transform_body(ui, body, transformTuple):
    """Transform body in its parentComponent in Fusion360

    Use moveFeatures.createInput2() to transform the body.

    Input:
    . body: body object to transform
    . transformTuple:
      - transformOperation: 'translate' or 'rotate'
      - vector3D: translation vector or rotation axis vector
      - angle: rotation angle in radians
    Return:
    . None

    Uses ui to report faults via Fusion360 GUI.
    """
    transformOperation, vector3D, angle = transformTuple
    # Create a transform
    transform = create_transform_matrix3D(ui, transformOperation, vector3D, angle)
    # Create ObjectCollection for createInput2()
    objects = adsk.core.ObjectCollection.create()
    objects.add(body)
    # Create a move feature
    moveFeatures = body.parentComponent.features.moveFeatures
    moveFeatureInput = moveFeatures.createInput2(objects)
    moveFeatureInput.defineAsFreeMove(transform)
    # Do the transform
    moveFeatures.add(moveFeatureInput)
