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
validOperations = ['join', 'cut', 'intersect']
validAssemblyActions = ['import_sketch',
                        'import_sketches',
                        'create_plane',
                        'create_planes',
                        'create_loft',
                        'create_lofts',
                        'combine_bodies',
                        'combine_bodies_multiple',
                        'split_body',
                        'split_body_multiple']


def value_to_str(value, toAbs=True):
    """Convert scalar value into string.

    . Make value positive if toAbs = true, else keep '-' in string
    . Replace '.' by '_' in case of float value.
    """
    if toAbs:
        return str(abs(value)).replace('.', '_')
    else:
        return str(value).replace('.', '_')


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
    """Write profile sketches in fileLines into seperate CSV sketch files.

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
            # Pass on next fileLines until empty line of sketch in fileLines
            entries = get_file_line_entries(fLine)
            segmentType = entries[0]
            if segmentType in validSegmentTypes:
                # New segment line, only pass on segmentType, omit any other entries
                sketchLines.append(segmentType + '\n')
            else:
                # Line with values, pass on as is
                sketchLines.append(fLine)
        else:
            # Empty line marks end of sketch in fileLines
            # . Write sketch file
            print('write_profile_sketch_files: %s' % sketchFilename)
            with open(sketchFilename, 'w') as fp:
                fp.writelines(sketchLines)
                nofFiles += 1
            # . Prepare for next sketch in fileLines
            li = 0
            sketchLines = []
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
                        nofFiles += 2
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
            # Empty line marks end of sketch in fileLines, prepare for next
            # sketch in fileLines
            li = 0
            sketchLines = []
    return nofFiles


def determine_rail_point_xyz(planeNormal, planeOffset, railNormal, railOffset, a, b):
    """Determine rail point 3D coordinates

    Inputs:
    . planeNormal: 'x', 'y', or 'z' normal of profile sketch plane
    . planeOffset: x, y or z coordinate of profile sketch plane
    . railNormal: 'x', 'y', or 'z' normal of rail plane, must be != planeNormal
    . railOffset: x, y or z coordinate of rail sketch plane.
    . a, b: 2D point coordinates in the profile sketch plane
    Return:
    . rail point 3D coordinates tuple or None when there is no rail point for
      profile sketch plane point (a, b).
    """
    railPoint = None
    if planeNormal == 'x':
        x = planeOffset
        if railNormal == 'y' and a == railOffset:
            railPoint = (x, a, b)
        elif railNormal == 'z' and b == railOffset:
            railPoint = (x, a, b)
    elif planeNormal == 'y':
        y = planeOffset
        if railNormal == 'x' and a == railOffset:
            railPoint = (a, y, b)
        elif railNormal == 'z' and b == railOffset:
            railPoint = (a, y, b)
    elif planeNormal == 'z':
        z = planeOffset
        if railNormal == 'x' and a == railOffset:
            railPoint = (a, b, z)
        elif railNormal == 'y' and b == railOffset:
            railPoint = (a, b, z)
    return railPoint


def get_cross_rail_points(fileLines, planesNormal, railName, railNormal, railOffset):
    """Get cross rail points for segments with railName from multiple sketches
    in fileLines.

    A segment can have one or more railNames, so be part of multiple cross
    rails between profiles.

    Inputs:
    . fileLines: lines from a points file with multiple profile sketches, that
        contain rail points for railName
    . planesNormal: 'x', 'y', or 'z'; selects sketches with planeNormal ==
        planesNormal
    . railName: selects segments with railNames from fileLines
    . railNormal: 'x', 'y', or 'z'; must be != planesNormal
    . railOffset: selects points in segments with railNormal coordinate value ==
        railOffset in the railNormal plane
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
            planeNormal = entries[0]
            planeOffset = float(entries[1])
        elif fLine.strip():
            li += 1
            if planeNormal == planesNormal:
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
                    railPoint = determine_rail_point_xyz(planeNormal, planeOffset, railNormal, railOffset, a, b)
                    if railPoint:
                        railPoints.append(railPoint)
        else:
            # Empty line marks end of sketch in fileLines, prepare for next
            # sketch in fileLines
            li = 0
        # Remove duplicate points from list (not use list(set()), because it
        # does not preserve order)
        result = []
        [result.append(p) for p in railPoints if p not in result]
    return result


def write_cross_rail_points_sketch_file(planeNormal, planeOffset, segmentType, railPoints, filename):
    """Write rail of railPoints into sketch file.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . planeOffset: offset from origin plane
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
            fp.write(planeNormal + ', ' + str(planeOffset) + '\n')
            # Write points with segmentType
            fp.write(segmentType + '\n')
            for p in railPoints:
                if planeNormal == 'x':
                    a = p[1]
                    b = p[2]
                elif planeNormal == 'y':
                    a = p[0]
                    b = p[2]
                elif planeNormal == 'z':
                    a = p[0]
                    b = p[1]
                fp.write('%.2f, %.2f\n' % (a, b))  # use 0.01 mm resolution
            nofFiles += 1
    else:
        print('write_cross_rail_points_sketch_file: no points for %s' % filename)
    return nofFiles


def write_loft_files(fileLines):
    """Write lofts in fileLines into seperate loft CSV files.

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
            # Pass on next fileLines until empty line of loft in fileLines
            loftLines.append(fLine)
        else:
            # Empty line marks end of loft in fileLines
            # . Write loft file
            print('write_loft_files: %s' % loftFilename)
            with open(loftFilename, 'w') as fp:
                fp.writelines(loftLines)
                nofFiles += 1
            # . Prepare for next loft in fileLines
            li = 0
    return nofFiles


def write_plane_files(fileLines):
    """Write planes in fileLines into seperate plane CSV files.

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
            # Pass on next fileLines until empty line of plane in fileLines
            planeLines.append(fLine)
        else:
            # Empty line marks end of plane in fileLines
            # . Write plane file
            print('write_plane_files: %s' % planeFilename)
            with open(planeFilename, 'w') as fp:
                fp.writelines(planeLines)
                nofFiles += 1
            # . Prepare for next plane in fileLines
            li = 0
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
            # Pass on next fileLines until empty line of plane in fileLines
            combineLines.append(fLine)
        else:
            # Empty line marks end of plane in fileLines
            # . Write combine bodies file
            print('write_combine_bodies_files: %s' % combineFilename)
            with open(combineFilename, 'w') as fp:
                fp.writelines(combineLines)
                nofFiles += 1
            # . Prepare for next combine bodies section in fileLines
            li = 0
    return nofFiles


def write_split_body_files(fileLines):
    """Write split body sections in fileLines into seperate plane CSV files.

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
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'split':
                splitFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a split body section in fileLines contains
            # info for split body filename
            entries = get_file_line_entries(fLine)
            splitBodyName = entries[1]
            splitFilename = 'split_' + splitBodyName + '.csv'
            splitFilename = os.path.join(splitFolder, splitFilename)
            splitLines = []
            splitLines.append('split\n')  # write file type
            splitLines.append(fLine)  # pass on fLine
        elif fLine.strip():
            # Pass on next fileLines until empty line of plane in fileLines
            splitLines.append(fLine)
        else:
            # Empty line marks end of plane in fileLines
            # . Write split body file
            print('write_split_body_files: %s' % splitFilename)
            with open(splitFilename, 'w') as fp:
                fp.writelines(splitLines)
                nofFiles += 1
            # . Prepare for next split bodies section in fileLines
            li = 0
    return nofFiles


def write_assembly_files(fileLines):
    """Write assembly in fileLines into seperate assembly CSV files.

    Input:
    . fileLines: lines from file that define one or more assemblies
    Return: number of files written
    """
    li = 0
    nofFiles = 0

    # Find assemblys in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a assembly in fileLines contains:
            # . file type 'assembly',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = get_file_line_entries(fLine)
            fileType = entries[0]
            if fileType == 'assembly':
                assemblyFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a assembly in fileLines contains assembly filename
            assemblyName = fLine.strip()
            assemblyFilename = assemblyName + '.csv'
            assemblyFilename = os.path.join(assemblyFolder, assemblyFilename)
            assemblyLines = []
            assemblyLines.append('assembly\n')  # write file type
            assemblyLines.append(assemblyName + '\n')  # write assembly name
        elif fLine.strip():
            # Pass on next fileLines until empty line of assembly in fileLines
            assemblyLines.append(fLine)
        else:
            # Empty line marks end of assembly in fileLines
            # . Write assembly file
            print('write_assembly_files: %s' % assemblyFilename)
            with open(assemblyFilename, 'w') as fp:
                fp.writelines(assemblyLines)
                nofFiles += 1
            # . Prepare for next assembly in fileLines
            li = 0
    return nofFiles
