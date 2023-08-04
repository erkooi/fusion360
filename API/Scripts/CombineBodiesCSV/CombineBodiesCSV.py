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
# Date: 17 Jul 2023
"""Combine bodies in active component in Fusion360, as defined in combine
bodies csv file.

See API/libraries/combinebodies.py
"""

# Fusion360
import adsk.core
import adsk.fusion
import traceback
import importlib

# Import local from API\\libraries
from . import append_sys_path_libraries  # noqa: F401
import interface360
import utilities360
import combinebodies
importlib.reload(interface360)
importlib.reload(utilities360)
importlib.reload(combinebodies)


def run(context):
    """Run script as Fusion360 API\\Script."""
    ui = None
    try:
        title = 'Combine bodies from csv file'
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Get active component in the active design
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('No active Fusion design', title)
            return
        activeComponent = design.activeComponent

        # Prompt user for CSV filename
        filename = interface360.get_csv_filename(ui, title)
        if filename is None:
            return

        # Prompt user for combine result type
        prompt = 'Ok = Create component, Cancel = Create body'
        combineNewComponent = interface360.prompt_boolean_choice(ui, title, prompt)

        # Combine bodies from CSV file in activeComponent
        combinebodies.combine_bodies_from_csv_file(ui, title, filename, activeComponent, combineNewComponent)

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
