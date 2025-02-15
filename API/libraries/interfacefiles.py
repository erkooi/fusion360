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
"""Module to interface with files.
"""

import os.path
import math

# Lists of valid key words in CSV files for generating objects in Fusion360
validCombineOperations = ['cut', 'intersect', 'join']
validCsvFileTypes = ['assembly', 'combine', 'design', 'extrude', 'loft', 'mirror',
                     'modifyedges', 'movecopy', 'plane', 'revolve', 'sketch', 'split']
validCsvFileExtensions = validCsvFileTypes + ['corail', 'crossrail']
validLocalObjectTypes = ['body', 'plane', 'sketch']
validMirrorOperations = ['join', 'new_component', 'new_body']
validModifyEdgesOperations = ['chamfer', 'fillet', 'log_edges', 'log_faces']
validModifyEdgesItems = ['edges', 'faces']
validMovecopyObjects = ['body', 'component']
validMovecopyOperations = ['copy', 'light_bulb', 'move', 'translate', 'remove', 'rotate']
# . The order of actions in validOrderedActions matters. E.g. combine actions
#   have to be performed in order, because a combine action may dependent on a
#   previous combine result.
validOrderedActions = ['combine', 'extrude', 'mirror', 'modifyedges', 'movecopy', 'revolve', 'split']
validPlaneNormals = ['x', 'y', 'z']
validRailTypes = ['co_rail', 'cross_rails']
# . The order of actions in validRandomActions does not matter. The order
#   in which e.g. lofts are performed does not matter, because lofts do not
#   depend on other lofts and do not cut, intersect or join.
validRandomActions = ['loft', 'plane', 'sketch']
validSegmentTypes = ['arc', 'circle', 'ellipse', 'line', 'offset_curve', 'point', 'spline', 'textbox']
validSplitToolTypes = ['body', 'plane']
validUnits = ['mm', 'cm', 'm']

# For assembly create actions the order is dont care, for assembly run actions
# the order can matter.
validAssemblyActions = ['echo',
                        'create_loft',
                        'create_plane',
                        'create_sketch',
                        'multiple_create_loft',
                        'multiple_create_plane',
                        'multiple_create_sketch',
                        'run_combine',
                        'run_extrude',
                        'run_mirror',
                        'run_modifyedges',
                        'run_movecopy',
                        'run_revolve',
                        'run_split',
                        'multiple_run_combine',
                        'multiple_run_extrude',
                        'multiple_run_mirror',
                        'multiple_run_modifyedges',
                        'multiple_run_movecopy',
                        'multiple_run_revolve',
                        'multiple_run_split']


def value_to_str(value, toAbs=False, pointChar='.'):
    """Convert scalar value into string.

    If 1x, 10x, 100x, 1000x, ... float value is close to integer, then convert
    to integer string (0 decimals) or to float string with 1, 2, 3, ...
    decimals.

    maxNofDecimals:
    . Choose maxNofDecimals = 15, because 64 bit double can fit 15 decimals
    . Choose maxNofDecimals = 12, to have rel_tol=1e-12, abs_tol=1e-12, to
      be more accurate than Fusion360:
      - application.pointTolerance = 1.000000e-08 m = 10.000000 nm
      - application.vectorAngleTolerance = 1.000000e-10 rad = 5.729578e-09
        degrees

    math.isclose:
    . rel_tol: relative tolerance for math.isclose(), to compare values that
      are != 0
    . abs_tol: absolute tolerance for math.isclose(), to compare value to 0

    Input:
    . value: integer or float value
    . toAbs: make value positive if toAbs = true, else keep sign '-' in string
    . pointChar: replace '.' by pointChar in case of float value.

    Return:
    . value string with appropriate number of decimals
    """
    maxNofDecimals = 15
    tolerance = 1.0 / 10**maxNofDecimals
    # optional toAbs
    val = abs(value) if toAbs else value
    # determine number of decimals
    for nofDecimals in range(maxNofDecimals + 1):
        floatVal = 10**nofDecimals * val
        integerVal = int(round(floatVal))
        if math.isclose(floatVal, integerVal, rel_tol=tolerance, abs_tol=tolerance):
            break
    # convert to string
    valStr = '%.*f' % (nofDecimals, val)
    # convert -0 to 0
    if valStr == '-0':
        valStr = '0'
    # optional pointChar
    valStr = valStr.replace('.', pointChar)
    return valStr


def append_string_to_csv_line(inputLine, appendString, endOfLine='\n'):
    """Append comma appendString to inputLine

    Input:
    . inputLine: CSV input line string
    . appendString: string to append to inputLine
    Return:
    . outputLine: If appendString is enmpty string then return inputLine, else
      return with comma and appendString appended to inputLine. Append
      endOfLine to outputLine.
    """
    outputLine = inputLine
    if appendString:
        outputLine += ', ' + appendString
    outputLine += endOfLine
    return outputLine


def convert_entries_to_integers(entries):
    """Convert list of strings into list of integers."""
    return [int(s) for s in entries]


def convert_entries_to_floats(entries):
    """Convert list of strings into list of floats."""
    return [float(s) for s in entries]


def convert_csv_string_to_strings(csvString):
    """Convert comma separated string into list of stripped strings."""
    entries = csvString.split(',')
    return [s.strip() for s in entries]


def convert_entries_to_single_string(entries):
    """Convert list of strings into single string with comma's."""
    s = entries[0]
    for ei in entries[1:]:
        s += ', %s' % ei
    return s


def extract_object_name_and_extensions(filename):
    """Extract object name for e.g. sketch or plane from filename.

    For example:
                      objectName,  extensions
    . /a/b/c.csv   -> 'c',         ['csv']
    . /a/b/c.d.csv -> 'c',         ['d', 'csv']
    . /a/b/c       -> '',          [''], because a filename should have an
                                         extension
    . c.txt        -> 'c',         ['txt']
    . c.           -> 'c',         ['']
    . .txt         -> '',          ['txt']

    Input:
    . filename: filename with extension and optional directory.
    Return:
    . objectName: extracted name, or empty string when filename has no
      extension: list of extracted extension(s), or empty list when filename
      has no extensions.
    """
    # take part after last separator '/' in filename string, or filename string
    # if there is no separator '/' in filename string.
    basename = os.path.basename(filename)
    # remove extension
    basename = basename.split('.')
    objectName = ''
    extensions = ['']
    if len(basename) > 1:
        objectName = basename[0]
        extensions = basename[1:]
    return objectName, extensions


def extract_sub_folder_name(filename):
    """Extract sub folder name from last sub directory in filename.

    For example:
    . a/b/c.csv -> ('a', 'b')
    . /a/b/c.csv -> ('/a', 'b')
    . /a/b/c.d.csv -> ('/a', 'b')
    . /a/b/c -> ('/a/b', 'c')
    . c -> subFolderName = ('', 'c')
    . c.txt -> subFolderName = ('', '')

    Input:
    . filename: filename or directory name for file system pathnames
    Return:
    . dirname: remaining path to sub folder, or empty string when filename
      contains no more directory path
    . basename: extracted sub folder name, or empty string when filename
      contains no directory
    """
    # Directory name is last last part in filename, without the file name
    # . default assume last part (= basename) is the sub folder
    # . also keep remaining first part (= dirname)
    basename = os.path.basename(filename)  # last part
    dirname = os.path.dirname(filename)  # first part
    if '.' in basename:
        # . else if last part is a filename indicated by a dot, then get sub
        #   folder from last part (= basename) of first part (= dirname)
        basename = os.path.basename(dirname)  # last part of first part
        dirname = os.path.dirname(dirname)  # first part of first part
    return dirname, basename


def list_sub_folder_names(filename):
    """List sub folder names from sub directories path in filename.

    For example:
    . /a/b/c.csv -> subFolderNames = ['a', 'b']
    . /a/b/c.d.csv -> subFolderNames = ['a', 'b']
    . /a/b/c -> subFolderNames = ['a', 'b', 'c']
    . c -> subFolderNames = ['c']
    . c.txt -> subFolderNames = []

    Input:
    . filename: filename or directory name for file system pathnames
    Return:
    . subFolderNames: list of extracted sub folder names or empty string when
      filename contains no directory
    """
    subFolderNames = []
    dirname, basename = extract_sub_folder_name(filename)
    while basename:
        subFolderNames.append(basename)
        dirname, basename = extract_sub_folder_name(dirname)
    subFolderNames.reverse()
    return subFolderNames


def verify_component_folder_name(li, componentName, folderName):
    """Verify whether component name equals folder name in a timeline file

    Print WARNING message when last name in folderName and first name in
    componentName are not equal, to indicate that the action affects another
    group component than its own group component.

    Input:
    . li: line index in timeline file
    . componentName: name of component
    . folderName: name of sub folder with CSV files that define the component

    Return: True when names are equal, else False
    """
    subFolderNames = list_sub_folder_names(folderName)
    subComponentNames = list_sub_folder_names(componentName)
    if subFolderNames[-1] != subComponentNames[0]:
        print('WARNING line %d: first part in component name %s != %s last part in folder name' %
              (li, componentName, folderName))
        return False
    return True


def create_folder(folderName):
    """Create (sub)folder(s) if it not already exists and return path name.

    Input:
    . folderName: name of folder, or path and name of subfolder
    Return:
    . folder: created name of folder, or created path and name of sub folder
    """
    # Convert to path separators (/, \\) for local system
    folder = os.path.normpath(folderName)
    try:
        os.makedirs(folder)
        print('create_folder: %s' % folder)
    except FileExistsError:
        pass
    return folder


def get_list_of_files_in_folder(folderName, extension='.csv'):
    """Return list of filenames in folder with specified extension.

    Input:
    . folderName: full path and folder name
    . extension: search for files in folder name with this extension
    Return:
    . result: list of found file path names in folder
    """
    # Loop through names in folderName
    result = []
    for name in os.listdir(folderName):
        fullname = os.path.join(folderName, name)
        fullname = os.path.normpath(fullname)
        if os.path.isfile(fullname):
            _, ext = os.path.splitext(fullname)
            if ext == extension:
                # Found a file with matching extension
                result.append(fullname)
    return result


def read_data_lines_from_file(filename):
    """Read file and return the lines with data in fileLines.

    Remove comment lines,
    Remove comment from lines,
    Keep one empty line between sections with data,
    Keep or insert one empty line at end when file contains multiple sections,
      else remove empty line at end for file with only one section.

    Input:
    . filename: full path and name of file
    Return:
    . dataLines: read lines from file with data
    """
    # Read all lines from file
    with open(filename, 'r') as fp:
        fileLines = fp.readlines()

    # Remove comment lines and remove comment from fileLines
    dataLines = []
    for fLine in fileLines:
        if '#' not in fLine:
            # Keep line with only data and keep empty line
            dataLines.append(fLine)
        else:
            data = fLine.split('#')[0].rstrip()  # keep indent
            if len(data) > 0:
                # Keep data from line that have comment
                dataLines.append(data + '\n')

    # Remove empty lines at start of file
    for li, fLine in enumerate(dataLines):
        if fLine.strip():
            # found first not empty line at index li
            break
    dataLines = dataLines[li:]

    # Keep one empty line after each section to mark end of section
    removeEmptyLine = False
    li = 0
    for fLine in list(dataLines):  # use list() to loop original list
        if fLine.strip():
            # found section line
            li += 1
            removeEmptyLine = False
        else:
            # found empty line at index li
            if removeEmptyLine:
                # remove surplus empty line from dataLines
                dataLines.pop(li)
            else:
                # keep first empty line, but remove any surplus empty dataLines
                li += 1
                removeEmptyLine = True

    # If necessary add empty line to mark end of last section in dataLines
    if dataLines[-1].strip():
        dataLines.append('')

    # Count number of sections
    sectionCnt = 0
    sectionPart = False
    for fLine in dataLines:
        if fLine.strip():
            # found section line
            if not sectionPart:
                sectionCnt += 1
                sectionPart = True
        else:
            # found empty line
            sectionPart = False

    # If file only has one section, then remove empty last line
    if sectionCnt == 1:
        dataLines.pop(-1)
    return dataLines


def read_units_from_file_lines(fileLines):
    """Read units from fileLines of file.

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . units: read units, when supported in validUnits, else default to 'mm'
    """
    units = 'mm'  # default
    for li, fLine in enumerate(fileLines):
        entries = get_file_line_entries(fLine)
        lineWord = entries[0]
        if lineWord == 'units':
            units = entries[1]
            if units in validUnits:
                print('read_units_from_file_lines: %s' % units)
                return units
            else:
                print('ERROR line %d: invalid units' % li)
                return units
    print('read_units_from_file_lines: %s (default)' % units)
    return units


def get_file_line_entries(fLine):
    """Strip comma separated values from file line.

    . Split lines at comma to get the values,
    . Remove leading and trailing whitespace characters from the values.
    . Empty line results in entries = [''], so enties[0] exists and is empty
      string

    Input:
    . fLine: one line from file
    Return:
    . entries: list of stripped values from comma separated fLine
    """
    entries = fLine.split(',')
    entries = [e.strip() for e in entries]
    return entries


def put_file_line_entries(entries):
    """Put entries string values in comma separated order in file line.

    . Put commas between entry values
    . Put one trailing space after comma
    . Empty line when entries = ['']

    Input:
    . entries: list of string values to put in comma separated fLine
    Return:
    . fLine: one line from file
    """
    fLine = ''
    nofEntries = len(entries)
    for ei, entry in enumerate(entries):
        fLine += entry
        # comma between entries, not after last entry
        if ei < nofEntries - 1:
            fLine += ', '
    fLine += '\n'
    return fLine


def get_rail_names(entries, railType):
    """Get railNames for certain railType from entries list.

    The railType is one of validRailTypes. The entries after the railType are
    the rail names for that rail type.

    Return:
    . railNames: list of found rail names from entries, or empty list
    """
    railNames = []
    foundRailType = False
    for entry in entries:
        if entry == railType:
            foundRailType = True
        elif foundRailType:
            if entry in validRailTypes:
                foundRailType = False
            else:
                railNames.append(entry)
    return railNames


def convert_data_lines_to_lists(fileLines):
    """Convert fileLines into lineLists using comma as separator.

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . lineLists: list of lists of data values per read line
    """
    lineLists = []
    for fLine in fileLines:
        lineLists.append(get_file_line_entries(fLine))
    return lineLists


def write_co_rail_sketch_csv_files(fileLines, units):
    """Write co_rail CSV sketch files."""
    return determine_co_rail_sketch_csv_files(fileLines, units, writeFile=True)


def list_co_rail_sketch_csv_files(fileLines):
    """Make timeline list of co_rail CSV sketch files."""
    return determine_co_rail_sketch_csv_files(fileLines, units='', writeFile=False)


def determine_co_rail_sketch_csv_files(fileLines, units, writeFile=True):
    """Determine co rail sketches for segments with a co_rail name from sketches
    in fileLines.

    Inputs:
    . fileLines: lines from a timeline file with sketches, that contain
      segments with optional co_rail name.
    . units: units from validUnits
    . writeFile: when True write the co_rail CSV files, else create a list of
      the co_rail file headers for timeline purposes.
    Input:
    . fileLines: lines from file that define one or more profile sketches
    Return:
    . nofFiles if writeFile, else timelineList
    """
    li = 0
    sketchLines = []
    nofFiles = 0
    timelineList = []

    # Find sketches in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a sketch section in fileLines contains:
            # . CSV file type 'sketch',
            # . folder name for sketch CSV file,
            # . filename for sketch CSV file,
            # . optional name of group component
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'sketch':
                coRailFolderName = entries[1] + '_co_rails'
                sketchName = entries[2]
                groupComponentName = ''
                if len(entries) > 3:
                    groupComponentName = entries[3] + '_co_rails'
                li += 1
        elif li == 1:
            li += 1
            # Second line of a sketch in fileLines contains info for sketch filename
            entries = get_file_line_entries(fLine)
            # Ignore entries[0] = 'offset_plane'
            planeNormal = entries[1]
            planeOffset = entries[2]
            # Prepare for a co_rail sketch
            sketchLines = []
            coRailName = []
            coRailFilename = ''
            coRailLines = []
        elif fLine.strip():
            li += 1
            # Process segments in fileLines until empty line of sketch in fileLines
            entries = get_file_line_entries(fLine)
            segmentType = entries[0]
            if segmentType in validSegmentTypes:
                # Process previous co_rail sketch
                if coRailName:
                    if writeFile:
                        # Write co rail sketch file for previous segment
                        print('write_co_rail_sketch_csv_files: %s' % coRailFilename)
                        with open(coRailFilename, 'w') as fp:
                            fp.writelines(sketchLines)
                            fp.writelines(coRailLines)
                            nofFiles += 1
                    else:
                        # Make timeline list of co rail sketch files
                        timelineTuple = ('co_rails', coRailFilename, groupComponentName)
                        timelineList.append(timelineTuple)
                    # Prepare for next co_rail sketch
                    sketchLines = []
                    coRailName = []
                    coRailFilename = ''
                    coRailLines = []
                # Get name for next optional co_rail sketch
                coRailName = get_rail_names(entries[1:], 'co_rail')
                if coRailName:
                    # Use new segment as co_rail sketch
                    coRailFolderName = create_folder(coRailFolderName)
                    coRailSketchName = sketchName + '_' + coRailName[0]
                    # . initialize sketchLines
                    coRailSketchLine = 'sketch, ' + coRailSketchName
                    coRailSketchLine = append_string_to_csv_line(coRailSketchLine, groupComponentName)
                    sketchLines.append(coRailSketchLine)  # write co rail sketch line
                    if units in validUnits:
                        sketchLines.append(units + '\n')  # write units
                    sketchLines.append('offset_plane, ' + planeNormal + ', ' + planeOffset + '\n')
                    # . initialize coRailLines
                    coRailFilename = coRailSketchName + '.corail.csv'
                    coRailFilename = os.path.join(coRailFolderName, coRailFilename)
                    coRailFilename = os.path.normpath(coRailFilename)
                    coRailLines.append(segmentType + '\n')
            else:
                if coRailName:
                    # Line with segment values for co rail, pass on as is
                    coRailLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines, prepare for next
            # sketch section in fileLines
            li = 0
            sketchLines = []
    if writeFile:
        if nofFiles > 0:
            print('write_co_rail_sketch_csv_files: Wrote %d CSV files' % nofFiles)
        return nofFiles
    else:
        return timelineList


def determine_rail_point_xyz(profilePlaneNormal, profilePlaneOffset, railPlaneNormal, railPlaneOffset, a, b):
    """Determine rail point 3D coordinates

    Inputs:
    . profilePlaneNormal: 'x', 'y', or 'z' normal of profile sketch plane
    . profilePlaneOffset: x, y or z coordinate of profile sketch plane
    . railPlaneNormal: 'x', 'y', or 'z' normal of rail plane, must be != profilePlaneNormal
    . railPlaneOffset: x, y or z coordinate of rail sketch plane.
    . a, b: 2D point coordinates in the profile sketch plane
    Return:
    . rail point 3D coordinates tuple or None when there is no rail point for
      profile sketch plane point (a, b).
    """
    railPoint = None
    if profilePlaneNormal == 'x':
        x = profilePlaneOffset
        if railPlaneNormal == 'y' and a == railPlaneOffset:
            railPoint = (x, a, b)
        elif railPlaneNormal == 'z' and b == railPlaneOffset:
            railPoint = (x, a, b)
    elif profilePlaneNormal == 'y':
        y = profilePlaneOffset
        if railPlaneNormal == 'x' and a == railPlaneOffset:
            railPoint = (a, y, b)
        elif railPlaneNormal == 'z' and b == railPlaneOffset:
            railPoint = (a, y, b)
    elif profilePlaneNormal == 'z':
        z = profilePlaneOffset
        if railPlaneNormal == 'x' and a == railPlaneOffset:
            railPoint = (a, b, z)
        elif railPlaneNormal == 'y' and b == railPlaneOffset:
            railPoint = (a, b, z)
    return railPoint


def _get_cross_rails_rail_names(fLine, ln):
    """Get rail_names from fLine, for cross rails definitions.

    Input: File line fLine, at line number ln.
    Return: rail_names.
    """
    entries = get_file_line_entries(fLine)
    if entries[0] == 'rail_names':
        return entries[1:]  # OK
    else:
        print('ERROR line %d: missing rail_names' % ln)
        return []


def _get_cross_rails_plane_normal(fLine, ln, planeType):
    """Get plane_normal from fLine, for cross rails definitions.

    Input:
    . File line fLine, at line number ln.
    . Plane type is 'profile'or 'rail'.
    Return: plane type plane_normal
    """
    if planeType not in ['profile', 'rail']:
        print('ERROR line %d: invalid plane type for _get_cross_rails_plane_normal()' % ln)
        return ''
    entries = get_file_line_entries(fLine)
    if entries[0] == planeType + '_plane_normal':
        planeNormal = entries[1]
        if planeNormal not in validPlaneNormals:
            print('ERROR line %d: invalid %s plane normal %s.' % (ln, planeType, planeNormal))
            return ''
        return planeNormal  # OK
    else:
        print('ERROR line %d: missing %s_plane_normal' % (ln, planeType))
        return ''


def _get_cross_rails_rail_plane_offsets(fLine, ln):
    """Get rail_plane_offsets from fLine, for cross rails definitions.

    Input: File line fLine, at line number ln.
    Return: rail_plane_offsets
    """
    entries = get_file_line_entries(fLine)
    if entries[0] == 'rail_plane_offsets':
        railPlaneOffsets = convert_entries_to_floats(entries[1:])
        return railPlaneOffsets  # OK
    else:
        print('ERROR line %d: missing rail_plane_offsets' % ln)
        return []


def _get_cross_rails_rail_segment_type(fLine, ln):
    """Get rail_segment_type from fLine, for cross rails definitions.

    Input: File line fLine, at line number ln.
    Return: rail_segment_type
    """
    entries = get_file_line_entries(fLine)
    if entries[0] == 'rail_segment_type':
        railSegmentType = entries[1]
        if railSegmentType not in validSegmentTypes:
            print('ERROR line %d: invalid rail segment type %s.' % (ln, railSegmentType))
            return ''
        return railSegmentType  # OK
    else:
        print('ERROR line %d: missing rail_segment_type' % ln)
        return ''


def read_cross_rails_definitions(fileLines):
    """Read cross rails definitions from fileLines.

    Format for cross_rails definition section in fileLines:
    . cross_rails, <rails folder>
    . rail_names, <strings>
    . profile_plane_normal, <x, y, or z>
    . rail_plane_normal, <x, y, or z>
    . rail_plane_offsets, <integers>
    . rail_segment_type, <spline>

    Inputs:
    . fileLines: lines from a timeline file with cross rails definitions, that
      define profile sketches and cross rails between them.
    Return: List of crossRailsTuples():
      . railFolderName
      . groupComponentName
      . railNames[]
      . profilePlaneNormal
      . railPlaneNormal
      . railPlaneOffsets
      . railSegmentType
    """
    li = 0
    crossRailsTuples = []

    # Find cross rails definitions in fileLines, seperated by one empty line
    for ln, fLine in enumerate(fileLines):
        if li == 0:
            # First line of a cross_rails in fileLines contains:
            # . CSV file type 'cross_rails',
            # . folder name for cross_rails CSV files
            # . optional name of group component
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'cross_rails':
                railFolderName = create_folder(entries[1])
                groupComponentName = ''
                if len(entries) > 2:
                    groupComponentName = entries[2]
                    # verify_component_folder_name(li, groupComponentName, railFolderName)
                li += 1
        elif li == 1:
            li += 1
            railNames = _get_cross_rails_rail_names(fLine, ln)
        elif li == 2:
            li += 1
            profilePlaneNormal = _get_cross_rails_plane_normal(fLine, ln, 'profile')
        elif li == 3:
            li += 1
            railPlaneNormal = _get_cross_rails_plane_normal(fLine, ln, 'rail')
        elif li == 4:
            li += 1
            railPlaneOffsets = _get_cross_rails_rail_plane_offsets(fLine, ln)
        elif li == 5:
            li += 1
            railSegmentType = _get_cross_rails_rail_segment_type(fLine, ln)
            # Add cross_rails definition to crossRailsTuples list
            crossRailsTuple = (railFolderName, groupComponentName, railNames,
                               profilePlaneNormal, railPlaneNormal, railPlaneOffsets,
                               railSegmentType)
            crossRailsTuples.append(crossRailsTuple)
        elif fLine.strip():
            li += 1
            print('ERROR line %d: unexpected line in cross_rails section' % ln)
        else:
            # Empty line marks end of section in fileLines, prepare for next
            # cross_rails section in fileLines
            li = 0
    if len(crossRailsTuples) > 0:
        print('read_cross_rails_definitions: Found %d cross_rails sections' % len(crossRailsTuples))
    return crossRailsTuples


def get_cross_rail_points(fileLines, profilePlaneNormal, railName, railPlaneNormal, railPlaneOffset):
    """Get cross rail points for segments with railName from multiple sketches
    in fileLines.

    A segment can have one or more railNames, so be part of multiple cross
    rails between profiles.

    Inputs:
    . fileLines: lines from a timeline file with multiple profile sketches,
        that contain rail points for railName
    . profilePlaneNormal: 'x', 'y', or 'z'; selects sketches with
        sketchPlaneNormal == profilePlaneNormal
    . railName: selects segments with railNames from fileLines
    . railPlaneNormal: 'x', 'y', or 'z'; must be != profilePlaneNormal
    . railPlaneOffset: selects points in segments with railPlaneNormal
        coordinate value == railPlaneOffset in the railPlaneNormal plane
    Return:
    . result: list of rail points for railName
    """
    li = 0
    railPoints = []

    # Find sketches in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a sketch in fileLines contains file type 'sketch',
            # the folder name is not used to get_cross_rail_points().
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'sketch':
                li += 1
        elif li == 1:
            li += 1
            # Second line of a sketch in fileLines contains plane info for sketch,
            # the sketch name info is not used to get_cross_rail_points().
            entries = get_file_line_entries(fLine)
            # Ignore entries[0] = 'offset_plane'
            sketchPlaneNormal = entries[1]
            sketchPlaneOffset = float(entries[2])
        elif fLine.strip():
            li += 1
            if sketchPlaneNormal == profilePlaneNormal:
                # Parse line
                entries = get_file_line_entries(fLine)
                segmentType = entries[0]
                if segmentType in validSegmentTypes:
                    # New segment line, get optional cross rail names
                    crossRailNames = get_rail_names(entries[1:], 'cross_rails')
                elif railName in crossRailNames:
                    # Coordinates line, get rail point in crossRailNames
                    a = float(entries[0])
                    b = float(entries[1])
                    railPoint = determine_rail_point_xyz(sketchPlaneNormal, sketchPlaneOffset,
                                                         railPlaneNormal, railPlaneOffset, a, b)
                    if railPoint:
                        railPoints.append(railPoint)
        else:
            # Empty line marks end of section in fileLines, prepare for next
            # sketch section in fileLines
            li = 0
        # Remove duplicate points from list (not use list(set()), because it
        # does not preserve order)
        result = []
        [result.append(p) for p in railPoints if p not in result]
    return result


def write_cross_rail_sketch_csv_file(filename, railSketchName, groupComponentName, units,
                                     railPlaneNormal, railPlaneOffset, segmentType, railPoints):
    """Write rail of railPoints into sketch file.

    Input:
    . filename: full path and name of file
    . railSketchName: name of the cross_rail sketch
    . groupComponentName: group component for the cross_rail sketch
    . units: units from validUnits
    . railPlaneNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . railPlaneOffset: offset from origin plane
    . segmentType: string in validSegmentTypes in importsketch.py
    . railPoints: list of rail point coordinates (x, y, z) obtained from
        get_cross_rail_points()
    Return: number of files written
    """
    nofFiles = 0
    if len(railPoints) > 1:
        print('write_cross_rail_sketch_csv_file: %s' % filename)
        with open(filename, 'w') as fp:
            # Write file type
            sketchLine = 'sketch, ' + railSketchName
            sketchLine = append_string_to_csv_line(sketchLine, groupComponentName)
            fp.write(sketchLine)
            # Write units
            if units in validUnits:
                fp.write(units + '\n')
            # Write plane normal and offset
            fp.write('offset_plane, ' + railPlaneNormal + ', ' + str(railPlaneOffset) + '\n')
            # Write points with segmentType
            fp.write(segmentType + '\n')
            for p in railPoints:
                if railPlaneNormal == 'x':
                    a = p[1]
                    b = p[2]
                elif railPlaneNormal == 'y':
                    a = p[0]
                    b = p[2]
                elif railPlaneNormal == 'z':
                    a = p[0]
                    b = p[1]
                fp.write('%.2f, %.2f\n' % (a, b))  # use 0.01 mm resolution
            nofFiles = 1
    else:
        if nofFiles > 0:
            print('write_cross_rail_sketch_csv_file: no points for %s' % filename)
    return nofFiles


def write_cross_rail_sketch_csv_files(fileLines, units):
    """Get railPoints and write rail of railPoints into sketch file, for all
    cross_rails definitions in fileLines.

    Loop over all cross_rails definitions. Each cross_rails definition defines
    rails between profile sketches. The cross rails are in parallel planes.
    The list of cross_rails definitions are read from fileLines with
    read_cross_rails_definitions().

    Within a cross_rails defintion loop over railPlaneOffsets and then write
    one cross rail sketch file per each railName in railNames. Combines
    get_cross_rail_points() and write_cross_rail_sketch_csv_file() for list of
    railPlaneOffsets and railNames.

    Units from validUnits.
    """
    nofFiles = 0

    # Get cross_rails definitions
    crossRailsTuples = read_cross_rails_definitions(fileLines)

    # Process per cross_rails definition
    for crossRailsTuple in crossRailsTuples:
        # Extract cross_rails definition
        railFolderName, groupComponentName, railNames, \
                profilePlaneNormal, railPlaneNormal, railPlaneOffsets, railSegmentType = crossRailsTuple

        # Write CSV sketch files for cross_rails definition
        for railPlaneOffset in railPlaneOffsets:
            for railName in railNames:
                # Get railPoints
                railPoints = get_cross_rail_points(fileLines, profilePlaneNormal,
                                                   railName, railPlaneNormal, railPlaneOffset)
                # Construct filename
                railPlaneOffsetStr = value_to_str(railPlaneOffset, toAbs=True, pointChar='_')
                railSketchName = railPlaneNormal + '_' + railPlaneOffsetStr + '_' + railName
                filename = railSketchName + '.crossrail.csv'
                filename = os.path.join(railFolderName, filename)
                filename = os.path.normpath(filename)
                # Write sketch file
                nofFiles += write_cross_rail_sketch_csv_file(filename, railSketchName, groupComponentName, units,
                                                             railPlaneNormal, railPlaneOffset,
                                                             railSegmentType, railPoints)
        if nofFiles > 0:
            print('write_cross_rail_sketch_csv_files: Wrote %d CSV files in %s' % (nofFiles, railFolderName))
    return nofFiles


def _parse_first_fline(li, entries):
    """Extract folder/filename and first line for CSV file from fLine entries
    in fileLines.

    Input:
    . li, line number in fileLines
    . entries: Entries in first line of a CSV file section in fileLines, with:
      - fileType: CSV file type,
      - csvFolderName: folder name for fileType CSV file (not written in
        csvLines),
      - fileTypeFilename: filename for fileType CSV file,
      - groupComponentName: optional name of group component.
    Return:
    . csvFilename: csvFolderName/fileTypeFilename.csv for the CSV file
    . fileTypeLine: first line for in CSV file, without csvFolderName, and
      with:
      - fileType,
      - fileTypeFilename,
      - groupComponentName
    when OK, else return None
    """
    fileType = entries[0]
    if fileType not in validCsvFileTypes:
        print('ERROR line %d: unexpected fileType %s' % (li, fileType))
        return None
    csvFolderName = create_folder(entries[1])
    fileTypeFilename = entries[2]
    csvFilename = fileTypeFilename + '.' + fileType + '.csv'
    csvFilename = os.path.join(csvFolderName, csvFilename)
    csvFilename = os.path.normpath(csvFilename)
    groupComponentName = ''
    if len(entries) > 3:
        groupComponentName = entries[3]
        # verify_component_folder_name(li, groupComponentName, csvFolderName)
    fileTypeLine = fileType + ', ' + fileTypeFilename
    fileTypeLine = append_string_to_csv_line(fileTypeLine, groupComponentName)
    return csvFilename, fileTypeLine


def write_csv_files(fileLines, csvFileType, units=''):
    """Write csvFileType sections in fileLines into seperate CSV files.

    Input:
    . fileLines: lines from timeline file that define CSV file sections
    . csvFileType: specific CSV file type section to find and write
    . units: units from validUnits, or empty string when not applicable.
    Return: number of CSV files written
    """
    li = 0
    nofFiles = 0

    # Find CSV file sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # Parse first line of a CSV file section in fileLines.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == csvFileType:
                csvFilename, fileTypeLine = _parse_first_fline(li, entries)
                csvLines = []
                csvLines.append(fileTypeLine)  # write fileType line
                if units:
                    csvLines.append(units + '\n')  # write units
                li += 1
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            csvLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write CSV file
            with open(csvFilename, 'w') as fp:
                fp.writelines(csvLines)
                nofFiles += 1
            print('write_csv_files %s: %s' % (csvFileType, csvFilename))
            # . Prepare for next CSV section in fileLines
            li = 0
    if nofFiles > 0:
        print('write_csv_files %s: Wrote %d CSV files' % (csvFileType, nofFiles))
    return nofFiles


def write_assembly_csv_file(fileLines):
    """Write assembly section in fileLines into a CSV file.

    There can be maximum one assembly per filelines.

    Write assembly CSV file with:
    - First line: fileType, fileName, componentName
    - Next lines:
      . timeline actions from fileLines, one line per folder or per file
      . echo statements from fileLines in order of appearance

    Input:
    . fileLines: lines from timeline file that define CSV file sections
    Return: number of CSV files written
    """
    li = 0
    nofFiles = 0

    # Find CSV file sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # Parse first line of a CSV file section in fileLines.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'assembly':
                csvFilename, assemblyLine = _parse_first_fline(li, entries)
                csvLines = []
                csvLines.append(assemblyLine)  # write assembly line
                li += 1
        elif fLine.strip():
            # Skip on next fileLines until empty line in fileLines
            pass
        else:
            # Empty line marks end of section in fileLines
            # . Add timeline actions and echo lines for the assembly
            csvLines += read_timeline_from_file_lines(fileLines)
            # . Write CSV file
            with open(csvFilename, 'w') as fp:
                fp.writelines(csvLines)
                nofFiles += 1
            print('write_assembly_csv_file: %s' % csvFilename)
            # . Only support one assembly section per timeline fileLines
            break
    if nofFiles > 0:
        print('write_assembly_csv_file: Wrote %d CSV files' % nofFiles)
    return nofFiles


def write_design_csv_file(fileLines):
    """Write design section in fileLines into a CSV file.

    There can be maximum one design section per filelines.

    Write design CSV file with:
    - First line: fileType, fileName, componentName
    - Next lines:
      . assembly filenames, one line per per file
    - At end append all echo lines from fileLines

    Input:
    . fileLines: lines from timeline file that define CSV file sections
    Return: number of CSV files written
    """
    li = 0
    nofFiles = 0

    # Find CSV file sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # Parse first line of a CSV file section in fileLines.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'design':
                csvFilename, fileTypeLine = _parse_first_fline(li, entries)
                csvLines = []
                csvLines.append(fileTypeLine)  # write design line
                li += 1
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            csvLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Append echo lines from fileLines
            echoLines = _read_echo_lines_from_file_lines(fileLines)
            for echoLine in echoLines:
                csvLines.append(echoLine)
            # . Write CSV file
            with open(csvFilename, 'w') as fp:
                fp.writelines(csvLines)
                nofFiles += 1
            print('write_design_csv_file: %s' % csvFilename)
            # . Only support one design section per timeline fileLines
            break
    if nofFiles > 0:
        print('write_design_csv_file: Wrote %d CSV files' % nofFiles)
    return nofFiles


# Process planes and sketches per CSV folder, because planes and sketches do
# not depend on other objects.
# - get plane folders
# - get sketch folders
# - get sketch folders with co_rails is sketch folder name + '_co_rail'
# - get cross_rails sketches
# Process lofts per CSV folder, because lofts only depend on sketches:
# - get loft folders
# Process other objects in order per CSV file, because for actions on objects
# can depend on other object.
# - get assembly, combine, extrude, mirror, modifyedges, movecopy, revolve,
#   split CSV files
#
# For folders use:
# . multiple_create_plane, folderName, groupName
# . multiple_create_sketch, folderName, groupName
# . multiple_create_loft, folderName, groupName
# For files use:
# . run_assembly, filename, groupName
# . run_combine, filename, groupName
# . run_extrude, filename, groupName
# . run_mirror, filename, groupName
# . run_modifyedges, filename, groupName
# . run_movecopy, filename, groupName
# . run_revolve, filename, groupName
# . run_split, filename, groupName
def read_timeline_from_file_lines(fileLines):
    """Read timeline from fileLines of file.

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . timelineList: timeline list with assembly lines to create objects from:
      - CSV folders for which order in fileLines is don't care, or from
      - single CSV files in order of appearance in fileLines, with actions for
        which the order in fileLines does matter.
    """
    timelineList = []
    # Process per CSV folder
    timelineList += _read_timeline_multi_objects_from_file_lines(fileLines, 'sketch')
    timelineList += _read_timeline_multi_co_rails_sketches_from_file_lines(fileLines)
    timelineList += _read_timeline_multi_objects_from_file_lines(fileLines, 'cross_rails')
    timelineList += _read_timeline_multi_objects_from_file_lines(fileLines, 'loft')
    timelineList += _read_timeline_multi_objects_from_file_lines(fileLines, 'plane')
    # Remove duplicate multiple_create_sketch assembly lines from list, that
    # can occur when cross_rails use same folder as other sketches. Do not use
    # list(set()), because set() does not preserve order.
    result = []
    [result.append(aLine) for aLine in timelineList if aLine not in result]
    timelineList = result

    # Process per single CSV file
    timelineList += _read_timeline_single_objects_from_file_lines(fileLines)
    return timelineList


def _read_timeline_multi_co_rails_sketches_from_file_lines(fileLines):
    """Read timeline for sketches co_rails components from fileLines of file.

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . timelineList: timeline list with assembly lines to create co_rails
      sketches from CSV sketch folders for which order is don't care.
    """
    timelineList = []
    # Find sketches co_rails components from fileLines
    coRailsList = list_co_rail_sketch_csv_files(fileLines)
    for coRailTuple in coRailsList:
        # Use sub folder relative to assembly CSV file
        _, subFolderName = extract_sub_folder_name(coRailTuple[1])
        subFolderName = os.path.normpath(subFolderName)
        assemblyLine = 'multiple_create_sketch'
        assemblyLine = append_string_to_csv_line(assemblyLine, subFolderName)
        if assemblyLine not in timelineList:
            timelineList.append(assemblyLine)
    return timelineList


def _read_timeline_multi_objects_from_file_lines(fileLines, sectionType):
    """Read timeline for components with sectionType from fileLines of file.

    Use for sectionType in validRandomActions or 'cross_rails'. For cross_rails
    use sketch.

    Input:
    . fileLines: read lines from comma separate values file
    . sectionType: action section type in fileLines
    Return:
    . timelineList: timeline list with assembly lines to create objects from
      CSV folders for which order in fileLines is don't care. When error, then
      return None.
    """
    # Check input sectionType
    validTypes = validRandomActions + ['cross_rails']
    if sectionType not in validTypes:
        print('ERROR: invalid sectionType %s for multiple, random timeline actions' % sectionType)
        return None

    # Find components with sectionType
    timelineList = []
    for li, fLine in enumerate(fileLines):
        entries = get_file_line_entries(fLine)
        lineWord = entries[0]
        if lineWord == sectionType:
            # Use sub folder relative to assembly CSV file
            folderName = entries[1]
            _, subFolderName = extract_sub_folder_name(folderName)
            # Name of action type
            if sectionType in validRandomActions:
                # Define multiple actions for sectionType
                assemblyLine = 'multiple_create_%s' % sectionType
            elif sectionType == 'cross_rails':
                # Use sketch for multiple actions when sectionType is
                # cross_rails
                assemblyLine = 'multiple_create_sketch'
            assemblyLine = append_string_to_csv_line(assemblyLine, subFolderName)
            if assemblyLine not in timelineList:
                timelineList.append(assemblyLine)
    return timelineList


def _read_timeline_single_objects_from_file_lines(fileLines):
    """Read timeline for single objects from fileLines of file.

    Use for 'echo', or for actions in validOrderedActions that depend on
    their order in the timeline.

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . timelineList: timeline list with assembly lines to create objects from
      single CSV file in order of appearance in fileLines
    """
    # Find components with sectionType
    timelineList = []
    for li, fLine in enumerate(fileLines):
        entries = get_file_line_entries(fLine)
        lineWord = entries[0]
        if lineWord == 'echo':
            assemblyLine = 'echo, ' + convert_entries_to_single_string(entries[1:]) + '\n'
            timelineList.append(assemblyLine)
        elif lineWord in validOrderedActions:
            sectionType = lineWord
            # Use sub folder relative to assembly CSV file
            folderName = entries[1]
            _, subFolderName = extract_sub_folder_name(folderName)
            # Name of action file
            filename = entries[2] + '.' + sectionType + '.csv'
            filename = os.path.join(subFolderName, filename)
            filename = os.path.normpath(filename)
            assemblyLine = ('run_%s, ' % sectionType) + filename + '\n'
            if assemblyLine not in timelineList:
                timelineList.append(assemblyLine)
        # else: skip all other lines
    return timelineList


def _read_echo_lines_from_file_lines(fileLines):
    """Read echo lines from fileLines of file.

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . echoLines: list of echo statements in fileLines
    """
    # Find components with sectionType
    echoLines = []
    for li, fLine in enumerate(fileLines):
        entries = get_file_line_entries(fLine)
        lineWord = entries[0]
        if lineWord == 'echo':
            assemblyLine = 'echo, ' + convert_entries_to_single_string(entries[1:]) + '\n'
            echoLines.append(assemblyLine)
    return echoLines
