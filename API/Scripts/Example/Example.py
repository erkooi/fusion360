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
        interface360.print_text(ui, 'New run')

        # Get active component in the active design
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('No active Fusion design', title)
            return
        rootComponent = design.rootComponent
        activeComponent = design.activeComponent

        # Print component names
        interface360.print_text(ui, 'Root component name: ' + rootComponent.name)
        interface360.print_text(ui, 'Active component name: ' + activeComponent.name)

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
