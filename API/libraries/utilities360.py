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
# Get object based on component, indices, operation

def get_root_component(component):
    """Get rootComponent of component in design hierarchy.

    If the component itself is the root component, then also return the root
    component.

    Input:
    . component: component object
    Return:
    . rootComponent: root component in design hierarchy
    """
    rootComponent = component.parentDesign.rootComponent
    return rootComponent


def get_occurrence_anywhere(component, hostComponent=None, index=0):
    """Get occurrence of component anywhere.

    If hostComponent is None then search from rootComponent anywhere in design
    hierarchy, else only search anywhere in hostComponent.

    The last occurrence is the newest occurrence (with index = -1) or the only
    occurrence (then it has index = 0). Default assume there is only one
    occurrence, so use index = 0 or -1.

    Input:
    . component: component object
    . hostComponent: host component to search in for the component. If
      hostComponent is None, then search in the rootComponent.
    Return:
    . occurrence: occurrence of component in design hierarchy
    """
    if hostComponent is None:
        hostComponent = get_root_component(component)
    componentOccurrences = find_occurrences_anywhere(hostComponent, component.name)
    occurrence = componentOccurrences[index]
    return occurrence


def get_sketch_profiles_collection(ui, sketch, profileIndices):
    """Get objectCollection of sketch profiles with profileIndices in sketch

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


def get_body_faces_collection(ui, body, faceIndices):
    """Get objectCollection of body faces with faceIndices in body

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
# Find object based on object name

def extract_name_parts(objectName):
    """Extract the hierarchical parts from objectName.

    - The objectName can contain a components hierarchy, or a components
      hierarchy with a local object name or only a local object name
    - Use '/' as hierarchy separator.

    For example:
    . /a/b/c -> ['a', 'b', 'c']
    . a/b/c -> ['a', 'b', 'c']
    . c -> ['c']
    . '' -> []

    Input:
    . objectName: hierarchical name for a component or local object
    Return:
    . objectNameParts: list of name parts in objectName
    """
    objectNameParts = objectName.split('/')
    while '' in objectNameParts:
        # remove any empty string parts, that arise due to preceding, trailing
        # and double separatore in objectName string
        objectNameParts.remove('')
    return objectNameParts


def extract_last_part(objectName):
    """Extract last name part from objectName.

    - The objectName can contain a components hierarchy, or a components
      hierarchy with a local object name or only a local object name
    - Use '/' as hierarchy separator.

    For example:
    . /a/b/c -> c
    . a/b/c -> c
    . c -> c
    . '' -> None

    Input:
    . objectName: hierarchical name for an object.
    Return:
    . last name part in objectName, or None
    """
    objectNameParts = extract_name_parts(objectName)
    if len(objectNameParts) > 0:
        return objectNameParts[-1]
    else:
        return None


def find_search_component(ui, hostComponent, objectType, objectName):
    """Find search component for object with objectName

    If an optional specific object search component name is given in
    objectName, then use the search component with that name as
    searchComponent, else default use the hostComponent as searchComponent.

    Input:
    . hostComponent: default component object to search through
    . objectType: object type is 'component' or a local object from
      interfacefiles.validLocalObjectTypes.
    . objectName: object name to search for, with optional specific object
      search component name, separated by a slash
    Return:
    . searchComponent: search component when found, else None

    Uses ui to report faults via Fusion360 GUI.
    """
    verbosity = False

    # Default assume object with objectName is anywhere in hostComponent
    searchComponent = hostComponent

    # Check whether the objectName also specifies the search component of the
    # object
    searchComponentName = ''
    componentNameParts = extract_name_parts(objectName)

    # For objectType is 'component' objectName contains hierarchy of component
    # names, else for local objects in interfacefile.validLocalObjectTypes the
    # objectName contains hierarchy of component names and the local object
    # name.
    if objectType != 'component':
        # remove local object name from component names list
        componentNameParts.pop()
    interface360.print_text(ui, 'componentNameParts = ' + str(componentNameParts), verbosity)

    if len(componentNameParts) > 0:
        # Search for the component with searchComponentName anywhere in the
        # rootComponent. Searching from the rootComponent is suitable, because
        # component names are unique in the entire design.
        rootComponent = get_root_component(hostComponent)
        searchComponentName = componentNameParts[-1]
        searchComponent = find_component_anywhere(rootComponent, searchComponentName)
        if not searchComponent:
            # Specified search component of object not found
            return None
    interface360.print_text(ui, 'searchComponent.name = ' + searchComponent.name, verbosity)

    # Found the searchComponent
    return searchComponent


def find_sketch_anywhere(ui, hostComponent, sketchName):
    """Find (first) sketch with sketchName anywhere in hostComponent, or in the
    sketch search component name specified in sketchName.

    Input:
    . hostComponent: default component object to search through.
    . sketchName: sketch name to search for, with optional specific sketch
      search component name, separated by a slash
    Return:
    . sketch: sketch object when found, else None

    Uses ui to report faults via Fusion360 GUI.
    """
    # Find search component for sketch with sketchName
    searchComponent = find_search_component(ui, hostComponent, 'sketch', sketchName)
    if not searchComponent:
        # specified search component of sketch with sketchName not found
        return None

    # Extract name of the sketch
    sketchNamePart = extract_last_part(sketchName)

    # First look in searchComponent sketches
    sketches = searchComponent.sketches
    sketch = sketches.itemByName(sketchNamePart)
    if sketch:
        return sketch  # Found sketch

    # Then search further in the components of all occurrences
    occurrencesList = searchComponent.allOccurrences
    for i in range(0, occurrencesList.count):
        occurrence = occurrencesList.item(i)
        sketches = occurrence.component.sketches
        sketch = sketches.itemByName(sketchNamePart)
        if sketch:
            return sketch  # Found sketch
    # Sketch not found
    return None


def find_plane_anywhere(ui, hostComponent, planeName):
    """Find (first) plane with planeName anywhere in hostComponent, or in the
    plane search component name specified in planeName.

    The planeName can be the name of:
    . a custom plane
    . one of the three construction planes through the origin of the
      rootComponent:
      - rootXyConstructionPlane
      - rootXzConstructionPlane
      - rootYzConstructionPlane
    . one of the three construction planes through the origin of the
      hostComponent:
      - xYConstructionPlane
      - xZConstructionPlane
      - yZConstructionPlane

    Input:
    . hostComponent: defaut component object to search through.
    . planeName: plane name to search for, with optional specific plane
      search component name, separated by a slash
    Return:
    . plane: plane object when found, else None

    Uses ui to report faults via Fusion360 GUI.
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

    # Find search component for plane with planeName
    searchComponent = find_search_component(ui, hostComponent, 'plane', planeName)
    if not searchComponent:
        # specified search component of plane with planeName not found
        return None

    # Extract name of the plane
    planeNamePart = extract_last_part(planeName)

    # First look in searchComponent constructionPlanes
    constructionPlanes = searchComponent.constructionPlanes
    plane = constructionPlanes.itemByName(planeNamePart)
    if plane:
        return plane  # Found plane

    # Then search further in constructionPlanes in the components of all
    # occurrences
    occurrencesList = searchComponent.allOccurrences
    for i in range(0, occurrencesList.count):
        occurrence = occurrencesList.item(i)
        constructionPlanes = occurrence.component.constructionPlanes
        plane = constructionPlanes.itemByName(planeNamePart)
        if plane:
            return plane  # Found plane
    # Plane not found
    return None


def find_body_anywhere(ui, hostComponent, bodyName):
    """Find (first) body with bodyName anywhere in hostComponent, or in the
    body search component name specified in bodyName.

    Input:
    . hostComponent: default component object to search through
    . bodyName: body name to search for, with optional specific body search
      component name, separated by a slash
    Return:
    . body: body object when found, else None

    Uses ui to report faults via Fusion360 GUI.
    """
    # Find search component for body with bodyName
    searchComponent = find_search_component(ui, hostComponent, 'body', bodyName)
    if not searchComponent:
        # specified search component of body with bodyName not found
        return None

    # Extract name of the body
    bodyNamePart = extract_last_part(bodyName)

    # First look in searchComponent bodies
    body = searchComponent.bRepBodies.itemByName(bodyNamePart)
    if body:
        return body

    # Then search further in the component bRepBodies of all occurrences in the
    # searchComponent
    occurrencesList = searchComponent.allOccurrences
    for i in range(0, occurrencesList.count):
        occurrence = occurrencesList.item(i)
        body = occurrence.component.bRepBodies.itemByName(bodyNamePart)
        if body:
            return body  # Found body
    # Body not found
    return None


def find_bodies_collection_anywhere(ui, hostComponent, bodyNames):
    """Find objectCollection of bodies with bodyNames, anywhere in
    hostComponent, or in the component specified per bodyName in bodyNames.

    Input:
    . hostComponent: host component to search in for the bodies.
    . bodyNames: body names to look for, with optional specific search
      component name per bodyName in bodyNames
    Return:
    . result: True when all bodyNames were found, else False
    . bodies: ObjectCollection with found bodies

    Uses ui to report faults via Fusion360 GUI.
    """
    result = True
    bodies = adsk.core.ObjectCollection.create()
    for bodyName in bodyNames:
        body = find_body_anywhere(ui, hostComponent, bodyName)
        if body:
            bodies.add(body)
        else:
            interface360.error_text(ui, 'Body not found in path of body name %s and not in host component %s' %
                                    (bodyName, hostComponent.name))
            result = False
    return (result, bodies)


def find_occurrences_anywhere(hostComponent, componentName):
    """Find list of occurrence(s) with componentName anywhere in hostComponent.

    . If the hostComponent itself has componentName, then
      - if hostComponent is the rootComponent return the rootComponent as
        single occurrence
      - else return occurrences of hostComponent anywhere in rootComponent.
    . else return occurrences of componentName anywhere in hostComponent.

    Input:
    . hostComponent: host component to search in for the component.
    . componentName: occurrence name to search for
    Return:
    . occurrences: list of found occurrence objects or the rootComponent
    """
    # Extract name of the component
    componentNamePart = extract_last_part(componentName)

    # Check whether rootComponent is the occurrence, or else determine the
    # searchComponent for the occurrences
    occurrences = []
    rootComponent = get_root_component(hostComponent)
    if hostComponent.name == componentNamePart:
        if hostComponent == rootComponent:
            # If the rootComponent is the hostComponent and has componentName,
            # then return rootComponent as single occurrence
            occurrences.append(rootComponent)
            return occurrences
        else:
            # search in rootComponent for occurrences of the hostComponent
            # with componentName
            searchComponent = rootComponent
    else:
        # search in hostComponent for occurrences of the component with
        # componentName
        searchComponent = hostComponent

    # Search in searchComponent for all occurrences of the componentName
    occurrencesList = searchComponent.allOccurrences
    for i in range(0, occurrencesList.count):
        occurrence = occurrencesList.item(i)
        if componentNamePart == occurrence.component.name:
            # Found occurrence with componentName
            occurrences.append(occurrence)
    return occurrences


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
      or the hostComponent itself, if it has componentName.
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
    """Find objectCollection of components with componentNames, anywhere in
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
            interface360.error_text(ui,
                                    'Component not found in path of component name %s and not in host component %s' %
                                    (componentName, hostComponent.name))
            result = False
    return (result, components)


def find_occurrences_collection_anywhere(ui, hostComponent, componentNames):
    """Find objectCollection of occurrences with componentNames, anywhere
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
        if component:
            occurrence = get_occurrence_anywhere(component)
            occurrences.add(occurrence)
        else:
            interface360.error_text(ui,
                                    'Occurrence not found in path of component name %s and not in host component %s' %
                                    (componentName, hostComponent.name))
            result = False
    return (result, occurrences)


################################################################################
# Create object

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


def create_component_tree(hostComponent, componentName):
    """Create new component tree for componentName in hostComponent.

    Default put isLightBulbOn of new component occurrence on.

    Input:
    . hostComponent: host component for the new component tree
    . componentName: name for new component tree
    Return:
    . component object of the last new component in the component tree
    """
    # Extract name of the component
    componentNameParts = extract_name_parts(componentName)

    # Trace hierarchical path in componentName and create components if
    # necessary
    referenceComponent = hostComponent
    for componentNamePart in componentNameParts:
        component = find_component_anywhere(referenceComponent, componentNamePart)
        if component:
            # Continue with component
            referenceComponent = component
        else:
            # Create component for componentNamePart
            referenceComponent = create_component(referenceComponent, componentNamePart)
    # Return last component in componentName
    return referenceComponent


def find_or_create_component(hostComponent, componentName):
    """Find component with componentName in hostComponent or else create
       component with componentName in hostComponent.

    If componentName is empty string or is name of hostComponent then return
    hostComponent.

    If componentName is a hierarchy of components, then

    Default put isLightBulbOn of new component occurrence on in
    create_component().

    Input:
    . hostComponent: host component to search for the component
    . componentName: name or hierarchical name for the component
    Return:
    . component object of the component with componentName in hostComponent,
      or the hostComponent itself if it has componentName.
    """
    # Extract name of the component
    componentNamePart = extract_last_part(componentName)

    # If componentName is empty string, then return hostComponent as component
    if not componentNamePart:
        return hostComponent

    # If componentName is hostComponent name, then return hostComponent as
    # component
    if hostComponent.name == componentNamePart:
        return hostComponent

    # Look for componentName in rootComponent, because componentName must be
    # unique in the entire design
    rootComponent = get_root_component(hostComponent)
    component = find_component_anywhere(rootComponent, componentName)
    if not component:
        # Create new component in hostComponent
        component = create_component_tree(hostComponent, componentName)
    # else: Found occurrence of componentName in rootComponent
    return component


################################################################################
# Copy, move object in design hierarchy

def move_occurrence_into_occurrence(occurrence, targetOccurrence):
    """Move occurrence into targetOccurrence.

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


def copy_component_as_new_into_occurrence(component, targetOccurrence):
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
        newCopyOccurrence = move_occurrence_into_occurrence(newCopyOccurrence, targetOccurrence)
    return newCopyOccurrence


def remove_occurrence(occurrence):
    """Remove component occurrence from design."""
    component = occurrence.component
    rootComponent = get_root_component(component)
    removeFeatures = rootComponent.features.removeFeatures
    removeFeatures.add(occurrence)
    return True


def copy_body_to_occurrence(body, targetOccurrence):
    """Copy body to targetOccurrence.

    Input:
    . body: BRepBody object to copy
    . targetOccurrence: copy body to bodies in targetOccurrence, the
      targetOccurrence can be either the root component or an occurrence.
    Return:
    . copiedBody: BRepBody object of copied body
    """
    copiedBody = body.copyToComponent(targetOccurrence)
    return copiedBody


def move_body_to_occurrence(body, targetOccurrence):
    """Move body to targetOccurrence.

    Input:
    . body: BRepBody object to copy
    . targetOccurrence: move body to bodies in targetOccurrence, the
      targetOccurrence can be either the root component or an occurrence.
    Return:
    . movedBody: BRepBody object of moved body
    """
    movedBody = body.moveToComponent(targetOccurrence)
    return movedBody


def remove_body(body):
    """Remove body from design."""
    removeFeatures = body.parentComponent.features.removeFeatures
    removeFeatures.add(body)
    return True


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
            body = find_body_anywhere(ui, hostComponent, bodyName)
            if body:
                # Must use removeFeatures from parentComponent of body, this
                # can be hostComponent, but may also be a sub component within
                # hostComponent.
                removeFeatures = body.parentComponent.features.removeFeatures
                removeFeatures.add(body)
            else:
                interface360.error_text(ui,
                                        'Remove body not found in path of body name %s and not in host component %s' %
                                        (bodyName, hostComponent.name))
                return False
    return True


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
    Mechanisms b) and c) appear equivalent.

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
