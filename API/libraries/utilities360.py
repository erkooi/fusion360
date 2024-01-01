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

def find_sketch_anywhere(component, sketchName):
    """Find (first) sketch with sketchName anywhere in component.

    Input:
    . component: component object to search through
    . sketchName: sketch name to search for
    Return:
    . sketch: sketch object when found, else None
    """
    # First look in component sketches
    sketches = component.sketches
    for s in range(0, sketches.count):
        sketch = sketches.item(s)
        if sketch.name == sketchName:
            return sketch  # Found sketch
    # Then search further in all occurences
    occurrenceList = component.allOccurrences
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


def find_plane_anywhere(component, planeName):
    """Find (first) plane with planeName anywhere in component.

    Input:
    . component: component object to search through
    . planeName: plane name to search for
    Return:
    . plane: plane object when found, else None
    """
    # First look in component constructionPlanes
    constructionPlanes = component.constructionPlanes
    for s in range(0, constructionPlanes.count):
        plane = constructionPlanes.item(s)
        if plane.name == planeName:
            return plane  # Found plane
    # Then search further in all occurences
    occurrenceList = component.allOccurrences
    for i in range(0, occurrenceList.count):
        occurrence = occurrenceList.item(i)
        constructionPlanes = occurrence.component.constructionPlanes
        for s in range(0, constructionPlanes.count):
            plane = constructionPlanes.item(s)
            if plane.name == planeName:
                return plane  # Found plane
    # Plane not found
    return None


def find_body(component, bodyName):
    """Find body with bodyName in this component.

    Input:
    . component: component object to look in
    . bodyName: body name to look for
    Return:
    . body: body object when found, else None
    """
    return component.bRepBodies.itemByName(bodyName)


def find_body_anywhere(component, bodyName):
    """Find (first) body with bodyName anywhere in component.

    Input:
    . component: component object to search through, first look in bodies, then
      search in all occurrences.
    . bodyName: body name to search for
    Return:
    . body: body object when found, else None
    """
    # First look in component bodies
    body = find_body(component, bodyName)
    if body:
        return body
    # Then search further in all occurences
    occurrenceList = component.allOccurrences
    for i in range(0, occurrenceList.count):
        occurrence = occurrenceList.item(i)
        bRepBodies = occurrence.component.bRepBodies
        for s in range(0, bRepBodies.count):
            body = bRepBodies.item(s)
            if body.name == bodyName:
                return body  # Found body
    # Body not found
    return None


def find_bodies_collection_anywhere(ui, component, bodyNames):
    """Find collection of bodies that match the bodyNames, anywhere in
    component.

    Input:
    . component: component Bodies folder to look in
    . bodyNames: body names to look for
    Return:
    . result: True when all bodyNames were found, else False
    . bodies: ObjectCollection with found bodies

    Uses ui to report faults via Fusion360 GUI.
    """
    result = True
    bodies = adsk.core.ObjectCollection.create()
    for bodyName in bodyNames:
        body = find_body_anywhere(component, bodyName)
        if body:
            bodies.add(body)
        else:
            interface360.error_text(ui, 'Body %s not found in component %s' % (bodyName, component.name))
            result = False
    return (result, bodies)


def find_occurrences(hostComponent, componentName):
    """Find occurrence(s) with componentName anywhere in hostComponent.

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
    . hostComponent: host component object to search through
    . componentName: occurrence name to search for
    Return:
    . occurrences: list of found occurrence objects or the rootComponent
    """
    occurrences = []
    rootComponent = get_root_component(hostComponent)
    if hostComponent == rootComponent and componentName == hostComponent.name:
        # Found that the rootComponent is the hostComponent and has
        # componentName, so return rootComponent
        occurrences.append(rootComponent)
    else:
        occurrenceList = hostComponent.allOccurrences
        for i in range(0, occurrenceList.count):
            occurrence = occurrenceList.item(i)
            if componentName == occurrence.component.name:
                # Found occurrence with componentName
                occurrences.append(occurrence)
    return occurrences


def get_last_occurrence(component, hostComponent=None):
    """Get last occurrence of component.

    If hostComponent is None then search anywhere in design hierarchy, else
    only search anywhere in hostComponent.

    The last occurrence is the newest occurrence or the only occurrence.

    Input:
    . component: component object
    Return:
    . lastOccurrence: last occurrence of component in design hierarchy
    """
    if hostComponent is None:
        hostComponent = get_root_component(component)
    componentOccurrences = find_occurrences(hostComponent, component.name)
    lastOccurrence = componentOccurrences[-1]
    return lastOccurrence


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

def create_sketch_in_plane(component, sketchName, plane):
    """Create sketch in plane.

    Input:
    . component: place the sketch in component.
    . sketchName: name for the sketch
    . plane: plane object
    Return:
    . sketch: sketch object
    """
    # Create sketch in plane
    sketch = component.sketches.add(plane)
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


def create_component(hostComponent, componentName, isLightBulbOn=False):
    """Create new component with componentName in hostComponent.

    Input:
    . hostComponent: host component for the new component
    . componentName: name for new component
    . isLightBulbOn: when True put light bulb of new component occurrence on,
      else off
    Return:
    . component object of the new component
    """
    transform = adsk.core.Matrix3D.create()  # identity matrix
    occurrence = hostComponent.occurrences.addNewComponent(transform)
    occurrence.isLightBulbOn = isLightBulbOn
    occurrence.component.name = componentName
    return occurrence.component


def find_or_create_component(hostComponent, componentName, isLightBulbOn=False):
    """Find component with componentName in hostComponent or else create
       component with componentName in hostComponent. If componentName is
       name of hostComponent then return hostComponent.

    Input:
    . hostComponent: host component to search for the component
    . componentName: name for the component
    . isLightBulbOn: when True put light bulb of new component occurrence on,
      else off
    Return:
    . component object of the component with componentName in hostComponent,
      or the hostComponent itself if it has componentName.
    """
    # Check whether hostComponent has componentName
    if hostComponent.name == componentName:
        occurrence = hostComponent.occurrences[0]
        occurrence.isLightBulbOn = isLightBulbOn
        return hostComponent

    # Look for componentName in hostComponent
    occurrences = find_occurrences(hostComponent, componentName)
    if len(occurrences) == 0:
        # Create new component in hostComponent
        component = create_component(hostComponent, componentName, isLightBulbOn)
    else:
        # Found occurrence of componentName in hostComponent
        occurrence = occurrences[0]
        occurrence.isLightBulbOn = isLightBulbOn
        component = occurrence.component
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
      of occurences in a design.
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
    """Transform body in hostComponent in Fusion360

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
