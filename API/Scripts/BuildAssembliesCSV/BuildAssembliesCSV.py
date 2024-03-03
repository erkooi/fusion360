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
# Date: 2 Mar 2024
"""Build assembly CSV files from assemblies CSV file into a toplevel assembly
component in Fusion360.

See API/libraries/buildassemblies.py
"""

# Fusion360
import adsk.core
import adsk.fusion
import traceback
import importlib

# Import local from API\\libraries
from . import append_sys_path_libraries  # noqa: F401
import interfacefiles
import interface360
import utilities360
import schemacsv360
import importsketch
import createplane
import createloft
import combinebodies
import splitbody
import extrude
import movecopy
import mirror
import constructassembly
import buildassemblies
importlib.reload(interfacefiles)
importlib.reload(interface360)
importlib.reload(utilities360)
importlib.reload(schemacsv360)
importlib.reload(importsketch)
importlib.reload(createplane)
importlib.reload(createloft)
importlib.reload(combinebodies)
importlib.reload(splitbody)
importlib.reload(extrude)
importlib.reload(movecopy)
importlib.reload(mirror)
importlib.reload(constructassembly)
importlib.reload(buildassemblies)


def run(context):
    """Run script as Fusion360 API\\Script."""
    ui = None
    try:
        title = 'Build assembies from csv file'
        app = adsk.core.Application.get()
        ui = app.userInterface

        interface360.print_text(ui, 'New run', True)

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

        # Build assemblies from CSV file in activeComponent
        buildassemblies.build_assemblies_from_csv_file(ui, title, filename, activeComponent)

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
