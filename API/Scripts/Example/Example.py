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
# Date: 29 Jul 2023
"""Example script to demonstrate some script development basics Fusion360.
"""

import math

# Fusion360
import adsk.core
import adsk.fusion
import traceback
import importlib

# Import local from API\\libraries
from . import append_sys_path_libraries  # noqa: F401
import interface360
import utilities360
import samples360
importlib.reload(interface360)
importlib.reload(utilities360)
importlib.reload(samples360)


def run(context):
    """Run script as Fusion360 API\\Script."""
    ui = None
    try:
        title = 'Demonstrate print text in TEXT COMMAND box'
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Print in TEXT COMMAND box to indicate new run
        interface360.print_text(ui, 'New run - printed with: interface360.print_text()')
        adsk.core.Application.log('New run - printed with: adsk.core.Application.log()')

        # Get active component in the active design
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('No active Fusion design', title)
            return
        rootComponent = design.rootComponent
        activeComponent = design.activeComponent

        designType = 'direct' if design.designType == 0 else 'parametric'

        document = design.parentDocument
        application = document.parent  # = app

        # Create example component in rootComponent with example objects
        exampleComponent = utilities360.create_component(rootComponent, 'Example_component')
        objectsTuple = samples360.create_example_objects(exampleComponent)
        sketchTuple, extrudeTuple, planeTuple, mirrorTuple = objectsTuple
        sketch, profile = sketchTuple
        extrudeFeaturesInput, extrudeResult, extrudeBody, extrudeFace = extrudeTuple
        planeInput, planeResult = planeTuple
        mirrorInput, mirrorResult = mirrorTuple
        mirrorStitchToleranceModelParameter = mirrorResult.stitchTolerance

        ########################################################################
        # Print some design and component info

        interface360.print_text(ui, 'application.version %s' % application.version)
        interface360.print_text(ui, '. application.pointTolerance = %e m = %f nm' %
                                (application.pointTolerance / 100, application.pointTolerance * 10000000))
        interface360.print_text(ui, '. application.vectorAngleTolerance = %e rad = %e degrees' %
                                (application.vectorAngleTolerance, math.degrees(application.vectorAngleTolerance)))
        interface360.print_text(ui, '. mirrorStitchToleranceModelParameter.value = %e m = %f nm' %
                                (mirrorStitchToleranceModelParameter.value / 100,
                                 mirrorStitchToleranceModelParameter.value * 10000000))

        interface360.print_text(ui, 'document.name %s' % document.name)
        interface360.print_text(ui, '. document.version %s' % document.version)
        interface360.print_text(ui, '. document.objectType %s' % document.objectType)
        interface360.print_text(ui, '. document.products.count %d' % document.products.count)

        interface360.print_text(ui, 'product has no name')
        interface360.print_text(ui, '. product.objectType %s' % product.objectType)
        interface360.print_text(ui, '. product.productType %s' % product.productType)

        interface360.print_text(ui, 'design has no name')
        interface360.print_text(ui, '. design.objectType %s' % design.objectType)
        interface360.print_text(ui, '. design.designType %d = %s modelling' % (design.designType, designType))
        interface360.print_text(ui, '. design.allComponents.count %d:' % design.allComponents.count)

        interface360.print_text(ui, 'rootComponent.name %s' % rootComponent.name)
        interface360.print_text(ui, '. rootComponent.objectType %s' % rootComponent.objectType)
        interface360.print_text(ui, '. rootComponent.revisionId %s' % rootComponent.revisionId)
        interface360.print_text(ui, '. rootComponent.allOccurrences.count %d' % rootComponent.allOccurrences.count)

        interface360.print_text(ui, 'activeComponent.name %s' % activeComponent.name)
        interface360.print_text(ui, '. activeComponent.objectType %s' % activeComponent.objectType)
        interface360.print_text(ui, '. activeComponent.revisionId %s' % activeComponent.revisionId)
        interface360.print_text(ui, '. activeComponent.allOccurrences.count %d' % activeComponent.allOccurrences.count)
        interface360.print_text(ui, '')

        ########################################################################
        # List items in design

        # Print all component names.
        # . Component names are unique in the design.
        # . The design of a component is known via component.parentDesign
        # . A new empty component is made in the occurrences of a component via
        #   component.occurrences.addNewComponent(transform), where transform
        #   is an identy matrix3D.
        # . A new copy of a component first has to go via the root component
        #   using newOccurrence = rootComponent.occurrences.addNewComponentCopy
        #   (component, transform). Then the newOccurrence can be moved to the
        #   target component if necessary.
        # . For copy new component Fusion360 adds a postfix ' (index)' to
        #   original component name, to derive the default name for the new
        #   component.
        # . Sketches, bodies and planes in a component can be accessed via
        #   component.sketches, .bRepBodies and .contructionPlanes.
        interface360.print_text(ui, 'List of all component names in design.allComponents:')
        for item in range(design.allComponents.count):
            component = design.allComponents.item(item)
            interface360.print_text(ui, '    %s' % component.name)
        interface360.print_text(ui, '')

        # Print all occurrence names
        # . Occurrence names are unique in the design.
        # . Occurrence is created using copy paste of the component or by
        #   copy paste of an occurence of that component.
        # . The component of an occurrence is known via occurrence.component
        # . The new occurrence can be placed in any other component in the
        #   design, provided that the destination component does not include
        #   the occurrence, so no recursion (off course).
        # . An occurrence can be moved to another component using
        #   occurrence.moveToComponent()
        # . For copy paste component Fusion360 increments the index in postfix
        #   ':index' of the new occurrence.
        # . The occurrence.bRepBodies gives access to the bodies in the
        #   component.parentCOmponent of the occurrence.
        # . An occurrence can not be modified, but it can be transformed using
        #   occurrence.transform2 = matrix3D. The transform has to be a
        #   translation or an rotation, so no scaling because that would result
        #   in an modification.
        # . An occurrence can have its own additional sketches and components,
        #   but it seams only from the GUI, because there is no
        #   occurrence.sketches. If a sketch from the original component is
        #   modified via an occurrence in the GUI, then it affects the sketch
        #   in the original component, to keep the sketch the same in all
        #   occurrences of that component.
        interface360.print_text(ui, 'List of all occurrence names in root component:')
        for item in range(rootComponent.allOccurrences.count):
            occurrence = rootComponent.allOccurrences.item(item)
            interface360.print_text(ui, '    %s' % occurrence.name)
        interface360.print_text(ui, '')

        # Traverse design from root component for all occurrence names
        resultString = 'Hierarchy of all occurrence names in the root component:\n'
        resultString = samples360.traverseAssembly(rootComponent.occurrences.asList, 1, resultString)
        interface360.print_text(ui, resultString)
        interface360.print_text(ui, '')

        # Print occurrences in root component
        interface360.print_text(ui, 'List of the occurrence names in the root component:')
        for item in range(rootComponent.occurrences.count):
            occurrence = rootComponent.occurrences.item(item)
            interface360.print_text(ui, '    %s' % occurrence.name)
        interface360.print_text(ui, '')

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
