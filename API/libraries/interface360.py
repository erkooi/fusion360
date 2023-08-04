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
# Date: 7 may 2023
"""Module to interface user input and output with Fusion360.
"""

import adsk.core


def print_text(ui, message, verbosity=True):
    """Print message in Text Commands window of the Fusion360 GUI.

    Input:
    . ui: user interface object, to interact with user via Fusion360 GUI
    . message: text string to print in Text Commands window
    . verbosity: print when verbosity == True, else no print
    Return: None
    """
    if verbosity:
        # Get the palette that represents the Text Commands window.
        textPalette = ui.palettes.itemById('TextCommands')
        # Make sure the palette is visible.
        if not textPalette.isVisible:
            textPalette.isVisible = True
        # Write message
        textPalette.writeText(message)


def error_text(ui, message):
    """Print error message in Text Commands window of the Fusion360 GUI."""
    print_text(ui, message, verbosity=True)


def get_folder_name(ui, title):
    """Get folder name via Fusion360 GUI.

    Input:
    . ui: user interface object, to interact with user via Fusion360 GUI
    . title: title of dialog window
    Return:
    . folder: folder name when successful, else None
    """
    dialog = ui.createFolderDialog()
    dialog.title = title
    # Show folder dialog
    if dialog.showDialog() != adsk.core.DialogResults.DialogOK:
        return None
    else:
        return dialog.folder


def get_csv_filename(ui, title):
    """Get filename of CSV file via Fusion360 GUI.

    Input:
    . ui: user interface object, to interact with user via Fusion360 GUI
    . title: title of dialog window
    Return:
    . filename: file name when successful, else None
    """
    dialog = ui.createFileDialog()
    dialog.title = title
    dialog.filter = 'Comma Separated Values (*.csv);;All Files (*.*)'
    # Show file open dialog
    if dialog.showOpen() != adsk.core.DialogResults.DialogOK:
        return None
    else:
        return dialog.filename


def prompt_string(ui, title, prompt, string=''):
    """Prompt the user for a string when Ok, or empty string when Cancel.

    Input:
    . ui: user interface object, to interact with user via Fusion360 GUI
    . title: title of dialog window
    . prompt: request text to the user
    . string: default userInput string
    Return:
    . userInput string when not isCancelled, else return empty string
    """
    # Get userInput string and a Ok or Cancel from the user.
    userInput, isCancelled = ui.inputBox(prompt, title, string)

    # Parse user input, ignore userInput string
    if not isCancelled:
        return userInput
    else:
        return ''


def prompt_boolean_choice(ui, title, prompt):
    """Prompt the user for Ok = Yes or Cancel = No choice.

    Ignore userInput string, only use Ok and Cancel buttons status from
    isCancelled.

    Input:
    . ui: user interface object, to interact with user via Fusion360 GUI
    . title: title of dialog window
    . prompt: request text to the user
    Return:
    . True when not isCancelled, else False
    """
    # Get a Ok or Cancel from the user.
    userInput, isCancelled = ui.inputBox(prompt, title, '')

    # Parse user input, ignore userInput string
    return not isCancelled
