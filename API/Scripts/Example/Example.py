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
importlib.reload(interface360)


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

        # Print some design and component info
        interface360.print_text(ui, 'application.version %s' % application.version)
        interface360.print_text(ui, '. application.pointTolerance = %e m = %f nm' %
                                (application.pointTolerance / 100, application.pointTolerance * 10000000))
        interface360.print_text(ui, '. application.vectorAngleTolerance = %e rad = %e degrees' %
                                (application.vectorAngleTolerance, math.degrees(application.vectorAngleTolerance)))

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
        interface360.print_text(ui, '. design.allComponents.count %d' % design.allComponents.count)

        interface360.print_text(ui, 'rootComponent.name %s' % rootComponent.name)
        interface360.print_text(ui, '. rootComponent.objectType %s' % rootComponent.objectType)
        interface360.print_text(ui, '. rootComponent.revisionId %s' % rootComponent.revisionId)
        interface360.print_text(ui, '. rootComponent.allOccurrences.count %d' % rootComponent.allOccurrences.count)

        interface360.print_text(ui, 'activeComponent.name %s' % activeComponent.name)
        interface360.print_text(ui, '. activeComponent.objectType %s' % activeComponent.objectType)
        interface360.print_text(ui, '. activeComponent.revisionId %s' % activeComponent.revisionId)
        interface360.print_text(ui, '. activeComponent.allOccurrences.count %d' % activeComponent.allOccurrences.count)

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
