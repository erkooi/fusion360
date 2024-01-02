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

# Lists of valid key words in CSV files for generating objects in Fusion360
validFileTypes = ['sketch', 'plane', 'loft', 'combine', 'split', 'assembly']
validUnits = ['mm', 'cm']
validPlaneNormals = ['x', 'y', 'z']
validSegmentTypes = ['spline', 'line', 'arc', 'offset_curve', 'circle', 'point']
validRailTypes = ['co_rail', 'cross_rails']
validCombineOperations = ['join', 'cut', 'intersect']
validSplitToolTypes = ['plane', 'body']
validMoveObjects = ['component', 'body']
validMoveOperations = ['move', 'copy', 'remove', 'translate', 'rotate']
validAssemblyActions = ['echo',
                        'import_sketch',
                        'import_sketches',
                        'create_plane',
                        'create_planes',
                        'create_loft',
                        'create_lofts',
                        'extrude',
                        'extrudes',
                        'combine_bodies',
                        'combine_bodies_multiple',
                        'split_body',
                        'split_body_multiple']


def value_to_str(value, toAbs=True):
    """Convert scalar value into string.

    . Make value positive if toAbs = true, else keep '-' in string
    . Replace '.' by '_' in case of float value.
    . If float value is an integer, then convert to integer string
    """
    val = abs(value) if toAbs else value
    valStr = str(val).replace('.', '_')
    if valStr[-2:] == '_0':
        valStr = valStr[0:-2]
    return valStr


def convert_entries_to_integers(entries):
    """Convert list of strings into list of integers."""
    return [int(s) for s in entries]


def convert_entries_to_floats(entries):
    """Convert list of strings into list of floats."""
    return [float(s) for s in entries]


def convert_entries_to_single_string(entries):
    """Convert list of strings into single string with comma's."""
    s = entries[0]
    for ei in entries[1:]:
        s += ', %s' % ei
    return s


def extract_object_name(filename):
    """Extract object name for e.g. sketch or plane from filename.

    For example:
    . /a/b/c.csv -> objectName = 'c'
    . /a/b/c -> objectName = '', because filename should have an extension
    . c.txt -> objectName = 'c'

    Input:
    . filename: filename with extension and optional directory
    Return:
    . objectName: extracted name or empty string
    """
    # take part after last separator '/' in filename string, or filename string
    # if there is no separator '/' in filename string.
    basename = os.path.basename(filename)
    # remove extension
    objectName = basename.split('.')[0]
    extension = basename.split('.')[1]
    if extension:
        return objectName
    else:
        return ''


def extract_component_name(filepathname):
    """Extract component name from sub directory in filepathname.

    For example:
    . /a/b/c.csv -> componentName = 'b'
    . /a/b/c -> componentName = 'c'
    . c -> componentName = 'c'
    . c.txt -> componentName = ''

    Input:
    . filepathname: filename or directory name
    Return:
    . componentName: extracted name or empty string
    """
    # Directory name is last last part in filepathname, without the filename
    basename = os.path.basename(filepathname)
    if '.' in basename:
        dirname = os.path.dirname(filepathname)
        basename = os.path.basename(dirname)
    return basename


def create_folder(folderStr):
    """Create (sub)folder(s) if it not already exists and return path name.

    Input:
    . folderStr: name of folder, or path and name of subfolder
    Return:
    . folder: created name of folder, or created path and name of sub folder
    """
    # Convert to path separators (/, \\) for local system
    folder = os.path.normpath(folderStr)
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


def get_file_line_entries(fLine):
    """Strip comma separated values from file line.

    Split lines at comma to get the values,
    Remove leading and trailing whitespace characters from the values.

    Input:
    . fLine: one line from file
    Return:
    . entries: list of stripped values from comma separated fLine
    """
    entries = fLine.split(',')
    entries = [e.strip() for e in entries]
    return entries


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
    """Convert fileLines into dataLists using comma as separator.

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . dataLists: list of lists of data values per read line
    """
    dataLists = []
    for fLine in fileLines:
        dataLists.append(get_file_line_entries(fLine))
    return dataLists


def write_profile_sketch_files(fileLines):
    """Write profile sketches in fileLines into seperate CSV files.

    Sketch CSV files are put in folder specified per file.

    Input:
    . fileLines: lines from file that define one or more profile sketches
    Return: number of files written
    """
    li = 0
    sketchLines = []
    nofFiles = 0

    # Find sketches in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a sketch in fileLines contains:
            # . file type 'sketch',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'sketch':
                sketchFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a sketch in fileLines contains info for sketch filename
            entries = get_file_line_entries(fLine)
            planeNormal = entries[0]
            planeOffset = entries[1]
            sketchName = entries[2]
            po = str(abs(int(planeOffset)))
            sketchFilename = planeNormal + '_' + po + '_' + sketchName + '.csv'
            sketchFilename = os.path.join(sketchFolder, sketchFilename)
            sketchLines = []
            sketchLines.append('sketch\n')  # write file type
            sketchLines.append('mm\n')  # write units
            sketchLines.append(planeNormal + ', ' + planeOffset + '\n')
        elif fLine.strip():
            li += 1
            # Pass on next fileLines until empty line in fileLines
            entries = get_file_line_entries(fLine)
            segmentType = entries[0]
            if segmentType in validSegmentTypes:
                # New segment line, only pass on segmentType, omit any other entries
                sketchLines.append(segmentType + '\n')
            else:
                # Line with values, pass on as is
                sketchLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write sketch file
            print('write_profile_sketch_files: %s' % sketchFilename)
            with open(sketchFilename, 'w') as fp:
                fp.writelines(sketchLines)
                nofFiles += 1
            # . Prepare for next sketch in fileLines
            li = 0
            sketchLines = []
    print('Wrote %d csv files for %s' % (nofFiles, 'write_profile_sketch_files'))
    return nofFiles


def write_co_rail_sketch_files(fileLines):
    """Write co rail sketches for segments with a co_rail name from sketches
    in fileLines.

    Inputs:
    . fileLines: lines from a points file with sketches, that contain segments
        with optional co_rail name.
    Input:
    . fileLines: lines from file that define one or more profile sketches
    Return: number of files written
    """
    li = 0
    sketchLines = []
    nofFiles = 0

    # Find sketches in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a sketch in fileLines contains:
            # . file type 'sketch',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'sketch':
                coRailFolderStr = entries[1] + '_rails'
                li += 1
        elif li == 1:
            li += 1
            # Second line of a sketch in fileLines contains info for sketch filename
            entries = get_file_line_entries(fLine)
            planeNormal = entries[0]
            planeOffset = entries[1]
            sketchName = entries[2]
            po = str(abs(int(planeOffset)))
            sketchLines = []
            sketchLines.append('sketch\n')  # write file type
            sketchLines.append('mm\n')  # write units
            sketchLines.append(planeNormal + ', ' + planeOffset + '\n')
            coRailName = []
            coRailFilename = ''
            coRailLines = []
        elif fLine.strip():
            li += 1
            # Process segments in fileLines until empty line of sketch in fileLines
            entries = get_file_line_entries(fLine)
            segmentType = entries[0]
            if segmentType in validSegmentTypes:
                if coRailName:
                    # Write co rail sketch file for previous segment
                    print('write_co_rail_sketch_files: %s' % coRailFilename)
                    with open(coRailFilename, 'w') as fp:
                        fp.writelines(sketchLines)
                        fp.writelines(coRailLines)
                        nofFiles += 1
                # Get optional co_rail name
                coRailName = get_rail_names(entries[1:], 'co_rail')
                coRailFilename = ''
                coRailLines = []
                if coRailName:
                    # Use new segment as co rail
                    coRailFolder = create_folder(coRailFolderStr)
                    coRailFilename = planeNormal + '_' + po + '_' + sketchName + '_' + coRailName[0] + '.csv'
                    coRailFilename = os.path.join(coRailFolder, coRailFilename)
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
    print('Wrote %d csv files for %s' % (nofFiles, 'write_co_rail_sketch_files'))
    return nofFiles


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
        print('ERROR invalid plane type for _get_cross_rails_plane_normal()')
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
        print('ERROR line %d: missing rail_plane_offsets')
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
        print('ERROR line %d: missing rail_segment_type')
        return ''


def read_cross_rails_definitions(fileLines):
    """Read cross rails definitions from fileLines.

    Format for cross_rails definition section in fileLines:
    . cross_rails, <rails folder>, <optional rail filename prefix>
    . rail_names, <strings>
    . profile_plane_normal, <x, y, or z>
    . rail_plane_normal, <x, y, or z>
    . rail_plane_offsets, <integers>
    . rail_segment_type, <spline>

    Inputs:
    . fileLines: lines from a points file with cross rails definitions, that
      define profile sketches and cross rails between them.
    Return: List of crossRailsTuples():
      . railsFolder
      . railFilenamePrefix
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
            # . file type 'cross_rails',
            # . folder name for CSV files.
            # . optional prefix for rails filename.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'cross_rails':
                railsFolder = create_folder(entries[1])
                railFilenamePrefix = ''
                if len(entries) > 2:
                    railFilenamePrefix = entries[2]
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
            crossRailsTuple = (railsFolder, railFilenamePrefix, railNames,
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
    print('Found %d cross_rails sections by read_cross_rails_definitions' % len(crossRailsTuples))
    return crossRailsTuples


def get_cross_rail_points(fileLines, profilePlaneNormal, railName, railPlaneNormal, railPlaneOffset):
    """Get cross rail points for segments with railName from multiple sketches
    in fileLines.

    A segment can have one or more railNames, so be part of multiple cross
    rails between profiles.

    Inputs:
    . fileLines: lines from a points file with multiple profile sketches, that
        contain rail points for railName
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
            sketchPlaneNormal = entries[0]
            sketchPlaneOffset = float(entries[1])
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


def write_cross_rail_points_sketch_file(railPlaneNormal, railPlaneOffset, segmentType, railPoints, filename):
    """Write rail of railPoints into sketch file.

    Input:
    . railPlaneNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . railPlaneOffset: offset from origin plane
    . segmentType: string in validSegmentTypes in importsketch.py
    . railPoints: list of rail point coordinates (x, y, z) obtained from
        get_cross_rail_points()
    . filename: full path and name of file
    Return: number of files written
    """
    nofFiles = 0
    if len(railPoints) > 1:
        print('write_cross_rail_points_sketch_file : %s' % filename)
        with open(filename, 'w') as fp:
            # Write file type
            fp.write('sketch\n')
            # Write units
            fp.write('mm\n')
            # Write plane normal and offset
            fp.write(railPlaneNormal + ', ' + str(railPlaneOffset) + '\n')
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
            nofFiles += 1
    else:
        print('write_cross_rail_points_sketch_file: no points for %s' % filename)
    return nofFiles


def write_cross_rail_points_sketch_files(fileLines):
    """Get railPoints and write rail of railPoints into sketch file, for all
    cross_rails definitions in fileLines.

    Loop over all cross_rails definitions. Each cross_rails definition defines
    rails between profile sketches. The cross rails are in parallel planes.
    The list of cross_rails definitions are read from fileLines with
    read_cross_rails_definitions().

    Within a cross_rails defintion loop over railPlaneOffsets and then write
    one cross rail sketch file per each railName in railNames. Combines
    get_cross_rail_points() and write_cross_rail_points_sketch_file() for list
    of railPlaneOffsets and railNames.
    """
    nofFiles = 0

    # Get cross_rails definitions
    crossRailsTuples = read_cross_rails_definitions(fileLines)

    # Process per cross_rails definition
    for crossRailsTuple in crossRailsTuples:
        # Extract cross_rails definition
        railsFolder, railFilenamePrefix, railNames, \
                profilePlaneNormal, railPlaneNormal, railPlaneOffsets, railSegmentType = crossRailsTuple

        # Write CSV sketch files for cross_rails definition
        for railPlaneOffset in railPlaneOffsets:
            for railName in railNames:
                # Get railPoints
                railPoints = get_cross_rail_points(fileLines, profilePlaneNormal,
                                                   railName, railPlaneNormal, railPlaneOffset)
                # Construct filename
                filename = ''
                if railFilenamePrefix:
                    filename = railFilenamePrefix + '_'
                filename += railPlaneNormal + '_' + value_to_str(railPlaneOffset) + '_' + railName + '.csv'
                filename = os.path.join(railsFolder, filename)
                # Write sketch file
                nofFiles += write_cross_rail_points_sketch_file(railPlaneNormal, railPlaneOffset,
                                                                railSegmentType, railPoints, filename)
        print('Wrote %d csv files in %s with %s' % (nofFiles, railsFolder, 'write_cross_rail_points_sketch_files'))
    return nofFiles


def write_loft_files(fileLines):
    """Write lofts in fileLines into seperate CSV files.

    Input:
    . fileLines: lines from file that define one or more lofts
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find lofts in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a loft in fileLines contains:
            # . file type 'loft',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'loft':
                loftFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a loft in fileLines contains loft filename
            loftName = fLine.strip()
            loftFilename = loftName + '.csv'
            loftFilename = os.path.join(loftFolder, loftFilename)
            loftLines = []
            loftLines.append('loft\n')  # write file type
            loftLines.append(loftName + '\n')  # write loft name
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            loftLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write loft file
            print('write_loft_files: %s' % loftFilename)
            with open(loftFilename, 'w') as fp:
                fp.writelines(loftLines)
                nofFiles += 1
            # . Prepare for next loft section in fileLines
            li = 0
    print('Wrote %d csv files for %s' % (nofFiles, 'write_loft_files'))
    return nofFiles


def write_plane_files(fileLines):
    """Write planes in fileLines into seperate CSV files.

    Input:
    . fileLines: lines from file that define one or more planes
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find planes in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a plane in fileLines contains:
            # . file type 'plane',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'plane':
                planeFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a plane in fileLines contains plane filename
            planeName = fLine.strip()
            planeFilename = planeName + '.csv'
            planeFilename = os.path.join(planeFolder, planeFilename)
            planeLines = []
            planeLines.append('plane\n')  # write file type
            planeLines.append('mm\n')  # write units
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            planeLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write plane file
            print('write_plane_files: %s' % planeFilename)
            with open(planeFilename, 'w') as fp:
                fp.writelines(planeLines)
                nofFiles += 1
            # . Prepare for next plane section in fileLines
            li = 0
    print('Wrote %d csv files for %s' % (nofFiles, 'write_plane_files'))
    return nofFiles


def write_extrude_files(fileLines):
    """Write extrude sections in fileLines into seperate extrude CSV files.

    Input:
    . fileLines: lines from file that define one or more extrude sections
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find extrude sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a extrude section in fileLines contains:
            # . file type 'extrude',
            # . folder name for CSV file,
            # . filename for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'extrude':
                extrudeFolder = create_folder(entries[1])
                extrudeFilename = entries[2] + '.csv'
                extrudeFilename = os.path.join(extrudeFolder, extrudeFilename)
                extrudeLines = []
                extrudeLines.append('extrude\n')  # write file type
                extrudeLines.append('mm\n')  # write units
                li += 1
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            extrudeLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write extrude file
            print('write_extrude_files: %s' % extrudeFilename)
            with open(extrudeFilename, 'w') as fp:
                fp.writelines(extrudeLines)
                nofFiles += 1
            # . Prepare for next extrude section in fileLines
            li = 0
    print('Wrote %d csv files for %s' % (nofFiles, 'write_extrude_bodies_files'))
    return nofFiles


def write_combine_bodies_files(fileLines):
    """Write combine bodies sections in fileLines into seperate combine bodies CSV files.

    Input:
    . fileLines: lines from file that define one or more combine bodies sections
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find combine bodies sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a combine bodies section in fileLines contains:
            # . file type 'combine',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'combine':
                combineFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a combine bodies section in fileLines contains
            # combine bodies filename
            combineName = fLine.strip()
            combineFilename = combineName + '.csv'
            combineFilename = os.path.join(combineFolder, combineFilename)
            combineLines = []
            combineLines.append('combine\n')  # write file type
            combineLines.append(combineName + '\n')  # write combine name
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            combineLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write combine bodies file
            print('write_combine_bodies_files: %s' % combineFilename)
            with open(combineFilename, 'w') as fp:
                fp.writelines(combineLines)
                nofFiles += 1
            # . Prepare for next combine bodies section in fileLines
            li = 0
    print('Wrote %d csv files for %s' % (nofFiles, 'write_combine_bodies_files'))
    return nofFiles


def write_split_body_files(fileLines):
    """Write split body sections in fileLines into seperate CSV files.

    Input:
    . fileLines: lines from file that define one or more split body sections
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find split body sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a split body section in fileLines contains:
            # . file type 'split',
            # . folder name for CSV file.
            # . filename for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'split':
                splitFolder = create_folder(entries[1])
                splitFilename = entries[2] + '.csv'
                splitFilename = os.path.join(splitFolder, splitFilename)
                splitLines = []
                splitLines.append('split\n')  # write file type
                li += 1
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            splitLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write split body file
            print('write_split_body_files: %s' % splitFilename)
            with open(splitFilename, 'w') as fp:
                fp.writelines(splitLines)
                nofFiles += 1
            # . Prepare for next split bodies section in fileLines
            li = 0
    print('Wrote %d csv files for %s' % (nofFiles, 'write_split_body_files'))
    return nofFiles


def write_movecopy_files(fileLines):
    """Write move or copy sections in fileLines into seperate CSV files.

    Input:
    . fileLines: lines from file that define one or more move or copy sections
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find move or copy sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a move or copy section in fileLines contains:
            # . file type 'movecopy',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'movecopy':
                moveCopyFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a move or copy section in fileLines contains
            # info for move or copy filename
            entries = get_file_line_entries(fLine)
            objectType = entries[0]
            objectName = entries[1]
            moveCopyFilename = 'movecopy_' + objectType + '_' + objectName + '.csv'
            moveCopyFilename = os.path.join(moveCopyFolder, moveCopyFilename)
            moveCopyLines = []
            moveCopyLines.append('movecopy\n')  # write file type
            moveCopyLines.append('mm\n')  # write units
            moveCopyLines.append(objectType + ', ' + objectName + '\n')  # write object type
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            moveCopyLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write move or copy file
            print('write_movecopy_files: %s' % moveCopyFilename)
            with open(moveCopyFilename, 'w') as fp:
                fp.writelines(moveCopyLines)
                nofFiles += 1
            # . Prepare for next move or copy section in fileLines
            li = 0
    print('Wrote %d csv files for %s' % (nofFiles, 'write_movecopy_files'))
    return nofFiles


def write_assembly_files(fileLines):
    """Write assembly in fileLines into seperate assembly CSV files.

    Input:
    . fileLines: lines from file that define one or more assemblies
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find assemblies in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a assembly in fileLines contains:
            # . file type 'assembly',
            # . folder name for CSV file.
            # . filename for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'assembly':
                assemblyFolder = create_folder(entries[1])
                assemblyFilename = entries[2] + '.csv'
                assemblyFilename = os.path.join(assemblyFolder, assemblyFilename)
                assemblyLines = []
                assemblyLines.append('assembly\n')  # write file type
                li += 1
        elif fLine.strip():
            # Pass on next fileLines until empty line in fileLines
            assemblyLines.append(fLine)
        else:
            # Empty line marks end of section in fileLines
            # . Write assembly file
            print('write_assembly_files: %s' % assemblyFilename)
            with open(assemblyFilename, 'w') as fp:
                fp.writelines(assemblyLines)
                nofFiles += 1
            # . Prepare for next assembly section in fileLines
            li = 0
    print('Wrote %d csv files for %s' % (nofFiles, 'write_assembly_files'))
    return nofFiles
