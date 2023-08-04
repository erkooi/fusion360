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


def find_sketch(component, sketchName):
    """Find (first) sketch with sketchName anywhere in component.

    Input:
    . component: component object to search through
    . sketchName: sketch name to search for
    Return:
    . sketch: sketch object when found, else None
    """
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


def find_plane(component, planeName):
    """Find (first) plane with planeName anywhere in component.

    Input:
    . component: component object to search through
    . planeName: plane name to search for
    Return:
    . plane: plane object when found, else None
    """
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
    """Find (first) body with bodyName anywhere in component.

    Input:
    . component: component object to search through
    . bodyName: body name to search for
    Return:
    . body: body object when found, else None
    """
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


def find_bodies_collection(ui, component, bodyNames):
    """Find collection of bodies in component that match the bodyNames

    Input:
    . component: component Bodies folder to look in
    . bodyNames: body names to look for
    Return:
    . result: True when all bodyNames were found, else False
    . bodies: ObjectCollection with found bodies

    Uses ui, title, filename to report faults via Fusion360 GUI.
    """
    result = True
    bodies = adsk.core.ObjectCollection.create()
    for bodyName in bodyNames:
        body = component.bRepBodies.itemByName(bodyName)
        if body:
            bodies.add(body)
        else:
            interface360.error_text(ui, 'Body %s not found in component %s' % (bodyName, component.name))
            result = False
    return (result, bodies)


def find_occurrences(component, componentName):
    """Find occurrence(s) with componentName anywhere in component.

    Input:
    . component: component object to search through
    . componentName: occurrence name to search for
    Return:
    . occurrences: list of found occurrence objects
    """
    occurrences = []
    occurrenceList = component.allOccurrences
    for i in range(0, occurrenceList.count):
        occurrence = occurrenceList.item(i)
        if componentName in occurrence.component.name:
            occurrences.append(occurrence)  # Found occurrence
    return occurrences


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
    return None


def create_component(parentComponent, componentName, isLightBulbOn=False):
    """Create new component with componentName in parentComponent.

    Input:
    . parentComponent: parent component for the new component
    . componentName: name for new component
    . isLightBulbOn: when True put light bulb of new component occurrence on, else off
    Return:
    . component object of the new component
    """
    transform = adsk.core.Matrix3D.create()  # identity matrix
    occurrence = parentComponent.occurrences.addNewComponent(transform)
    occurrence.isLightBulbOn = isLightBulbOn
    occurrence.component.name = componentName
    return occurrence.component


def find_or_create_component(parentComponent, componentName, isLightBulbOn=False):
    """Find component with componentName in parentComponent or else create
       component with componentName in parentComponent.

    Input:
    . parentComponent: parent component to search for the component
    . componentName: name for the component
    . isLightBulbOn: when True put light bulb of new component occurrence on,
      else off
    Return:
    . component object of the component with componentName in parentComponent
    """
    occurrences = find_occurrences(parentComponent, componentName)
    if len(occurrences) == 0:
        # Create new component in parentComponent
        component = create_component(parentComponent, componentName, isLightBulbOn)
    else:
        # Found occurrence of componentName in parentComponent
        occurrence = occurrences[0]
        component = occurrence.component
    return component


def get_root_component(component):
    """Get rootComponent of component in design hierarchy

    Input:
    . component : component object
    Return:
    . rootComponent: root component in design hierarchy
    """
    rootComponent = component.parentDesign.rootComponent
    return rootComponent


def get_last_occurrence(component):
    """Get last occurrence of component anywhere in design hierarchy.

    The last occurrence is the newest occurrence or the only occurrence.

    Input:
    . component : component object
    Return:
    . lastOccurrence: last occurrence of component in design hierarchy
    """
    rootComponent = get_root_component(component)
    componentOccurrences = find_occurrences(rootComponent, component.name)
    lastOccurrence = componentOccurrences[-1]
    return lastOccurrence


def move_occurrence(occurrence, targetOccurrence):
    """Move occurrence to targetOccurrence.

    Input:
    . occurrence : Occurrence object to copy
    . targetOccurrence : move occurrence to targetOccurrence
    Return:
    . movedOccurrence: Occurrence object of moved occurrence
    """
    movedOccurrence = occurrence.moveToComponent(targetOccurrence)
    return movedOccurrence


def copy_body(body, target):
    """Copy body to target.

    Input:
    . body : BRepBody object to copy
    . target : copy body to bodies in target, target can be an occurrence
      or the rootComponent
    Return:
    . copiedBody: BRepBody object of copied body
    """
    copiedBody = body.copyToComponent(target)
    return copiedBody


def move_body(body, target):
    """Move body to target.

    Input:
    . body : BRepBody object to copy
    . target : move body to bodies in target, target can be an occurrence
      or the rootComponent
    Return:
    . movedBody: BRepBody object of moved body
    """
    movedBody = body.moveToComponent(target)
    return movedBody


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
