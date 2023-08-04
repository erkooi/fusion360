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
# Date: 17 Mar 2023
"""Create F35b assembly from csv files in Fusion360

Uses API/libraries/ to create planes, sketches and lofts from CSV files
Uses CSV files generated with f35b_points.py
"""

import os.path

# Fusion360
import adsk.core
import adsk.fusion
import traceback
import importlib

# Import local from API\\libraries
from . import append_sys_path_libraries  # noqa: F401
import interface360
import utilities360
import importsketch
import createplane
import createloft
import combinebodies
import splitbody
importlib.reload(interface360)
importlib.reload(utilities360)
importlib.reload(importsketch)
importlib.reload(createplane)
importlib.reload(createloft)
importlib.reload(combinebodies)
importlib.reload(splitbody)


def run(context):
    """Run script as Fusion360 API\\Script."""
    ui = None
    try:
        title = 'Create F35B assembly from csv files'
        app = adsk.core.Application.get()
        ui = app.userInterface

        interface360.print_text(ui, 'New run', True)

        # Get all components in the active design
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('No active Fusion design', title)
            return

        # Prompt user for folder name
        csvFolderName = interface360.get_folder_name(ui, title)
        if csvFolderName is None:
            return

        # Create F35B assembly component in activeComponent
        activeComponent = design.activeComponent
        assemblyComponentName = 'F35B-CSV'
        assemblyComponent = utilities360.create_component(activeComponent, assemblyComponentName, isLightBulbOn=True)
        interface360.print_text(ui, '> Assemble component: ' + assemblyComponent.name)

        # Import sketches
        # . Use sub components, to be able control the light bulb per group in the GUI
        for groupComponentName in ['sketches_fuselage_x', 'sketches_rails_y', 'sketches_rails_z', 'sketches_wing',
                                   'sketches_cut_fuselage_x', 'sketches_cut_rails_y', 'sketches_cut_rails_z']:
            groupComponent = utilities360.create_component(assemblyComponent, groupComponentName, isLightBulbOn=False)
            folderName = os.path.join(csvFolderName, groupComponentName)
            interface360.print_text(ui, '> Create new component: ' + groupComponentName)
            importsketch.create_sketches_from_csv_files(ui, title, folderName, groupComponent)

        # Create lofts
        for groupName in ['loft_solids', 'loft_cuts']:
            folderName = os.path.join(csvFolderName, groupName)
            interface360.print_text(ui, '> Create lofts for: ' + groupName)
            createloft.create_lofts_from_csv_files(ui, title, folderName, assemblyComponent)

        # Create planes
        # . Use sub component, to avoid that the 3-point auxiliary sketches for the plane
        #   creation clutter the assemblyComponent Sketches folder.
        for groupComponentName in ['planes']:
            groupComponent = utilities360.create_component(assemblyComponent, groupComponentName, isLightBulbOn=False)
            folderName = os.path.join(csvFolderName, groupComponentName)
            interface360.print_text(ui, '> Create new component: ' + groupComponentName)
            createplane.create_planes_from_csv_files(ui, title, folderName, groupComponent)

        # Combine join bodies for split
        for groupName in ['combine_join_solids_for_split']:
            folderName = os.path.join(csvFolderName, groupName)
            interface360.print_text(ui, '> Combine join bodies for: ' + groupName)
            combinebodies.combine_bodies_from_csv_files(ui, title, folderName, assemblyComponent)

        # Split bodies
        for groupName in ['split_solids']:
            folderName = os.path.join(csvFolderName, groupName)
            interface360.print_text(ui, '> Split bodies for: ' + groupName)
            splitbody.split_bodies_from_csv_files(ui, title, folderName, assemblyComponent)

        # Combine join bodies
        for groupName in ['combine_join_bodies']:
            folderName = os.path.join(csvFolderName, groupName)
            interface360.print_text(ui, '> Combine join bodies for: ' + groupName)
            combinebodies.combine_bodies_from_csv_files(ui, title, folderName, assemblyComponent)

        # Combine cut shells
        for groupName in ['combine_cut_shells']:
            folderName = os.path.join(csvFolderName, groupName)
            interface360.print_text(ui, '> Combine cut bodies for: ' + groupName)
            combinebodies.combine_bodies_from_csv_files(ui, title, folderName, assemblyComponent)

        # Combine join shells
        for groupName in ['combine_join_shells']:
            folderName = os.path.join(csvFolderName, groupName)
            interface360.print_text(ui, '> Combine join bodies for: ' + groupName)
            combinebodies.combine_bodies_from_csv_files(ui, title, folderName, assemblyComponent)

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
