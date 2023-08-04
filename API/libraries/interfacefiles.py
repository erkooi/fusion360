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

validFileTypes = ['sketch', 'plane', 'loft', 'combine', 'split']
validOperations = ['join', 'cut', 'intersect']
validSegmentTypes = ['spline', 'line', 'offset_curve']


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
    Keep or insert one empty line at end

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
    return dataLines


def write_profile_sketch_files(fileLines):
    """Write profile sketches in fileLines into seperate CSV sketch files.

    Sketch CSV files are put in folder specified per file.

    Input:
    . fileLines: lines from file that define one or more profile sketches
    Return: None
    """
    li = 0
    sketchLines = []

    # Find sketches in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a sketch in fileLines contains:
            # . file type 'sketch',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
            fileType = entries[0]
            if fileType == 'sketch':
                sketchFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a sketch in fileLines contains info for sketch filename
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
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
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
            segmentType = entries[0]
            if segmentType in validSegmentTypes:
                # New segment line, only pass on segmentType, omit any other entries
                sketchLines.append(segmentType + '\n')
            else:
                # Values line, pass on as is
                sketchLines.append(fLine)
        else:
            # Empty line marks end of sketch in fileLines
            # . Write sketch file
            print('write_profile_sketch_files: %s' % sketchFilename)
            with open(sketchFilename, 'w') as fp:
                fp.writelines(sketchLines)
            # . Prepare for next sketch in fileLines
            li = 0
            sketchLines = []


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


def get_rail_points(fileLines, planesNormal, railName, railNormal, railOffset):
    """Get rail points from spline points in sketch profiles.

    Inputs:
    . fileLines: sketch rails in lines from a points file
    . planesNormal: 'x', 'y', or 'z'; selects sketches with planeNormal == planesNormal
    . railName: selects segments with railNames from fileLines
    . railNormal: 'x', 'y', or 'z'; must be != planesNormal
    . railOffset: selects points in segments with railNormal coordinate value ==
        railOffset in the railNormal plane
    Return:
    . result: list of rail points
    """
    li = 0
    railPoints = []

    # Find sketches in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a sketch in fileLines contains file type 'sketch', skip other lines
            if fLine.strip() == 'sketch':
                li += 1
            # First line of a sketch in fileLines contains file type 'sketch',
            # the folder name is not used to get_rail_points().
            # Skip lines for other file types.
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
            fileType = entries[0]
            if fileType == 'sketch':
                li += 1
        elif li == 1:
            li += 1
            # Second line of a sketch in fileLines contains plane info for sketch,
            # the sketch name info is not used to get_rail_points().
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
            planeNormal = entries[0]
            planeOffset = float(entries[1])
        elif fLine.strip():
            li += 1
            if planeNormal == planesNormal:
                # Parse line
                entries = fLine.split(',')
                entries = [e.strip() for e in entries]
                segmentType = entries[0]
                if segmentType in validSegmentTypes:
                    # New segment line, get optional railNames
                    railNames = entries[1:]
                elif railName in railNames:
                    # Coordinates line, get rail point in railNames
                    a = float(entries[0])
                    b = float(entries[1])
                    railPoint = determine_rail_point_xyz(planeNormal, planeOffset, railNormal, railOffset, a, b)
                    if railPoint:
                        railPoints.append(railPoint)
        else:
            # Empty line marks end of sketch in fileLines
            li = 0
        # Remove duplicate points from list (not use list(set()), because it
        # does not preserve order)
        result = []
        [result.append(p) for p in railPoints if p not in result]
    return result


def write_rail_sketch_file(planeNormal, planeOffset, segmentType, railPoints, filename):
    """Write loft rail of railPoints into sketch file.

    Input:
    . planeNormal: 'x' = yz-plane, 'y' = zx-plane, or 'z' = xy-plane
    . planeOffset: offset from origin plane
    . segmentType: string in validSegmentTypes in importsketch.py
    . railPoints: list of rail point coordinates (x, y, z) obtained from
        get_rail_points()
    . filename: full path and name of file
    Return: None
    """
    if railPoints:
        print('write_rail_sketch_file : %s' % filename)
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
    else:
        print('write_rail_sketch_file: no points for %s' % filename)


def write_loft_files(fileLines):
    """Write lofts in fileLines into seperate loft CSV files.

    Input:
    . fileLines: lines from file that define one or more lofts
    Return: None
    """
    li = 0

    # Find lofts in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a loft in fileLines contains:
            # . file type 'loft',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
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
            # . Prepare for next loft in fileLines
            li = 0


def write_plane_files(fileLines):
    """Write planes in fileLines into seperate plane CSV files.

    Input:
    . fileLines: lines from file that define one or more planes
    Return: None
    """
    li = 0

    # Find planes in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a plane in fileLines contains:
            # . file type 'plane',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
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
            # . Prepare for next plane in fileLines
            li = 0


def write_combine_bodies_files(fileLines):
    """Write combine bodies sections in fileLines into seperate combine bodies CSV files.

    Input:
    . fileLines: lines from file that define one or more combine bodies sections
    Return: None

    """
    li = 0

    # Find combine bodies sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a combine bodies section in fileLines contains:
            # . file type 'combine',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
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
            # . Prepare for next combine bodies section in fileLines
            li = 0


def write_split_body_files(fileLines):
    """Write split body sections in fileLines into seperate plane CSV files.

    Input:
    . fileLines: lines from file that define one or more split body sections
    Return: None
    """
    li = 0

    # Find split body sections in fileLines, seperated by one empty line
    for fLine in fileLines:
        if li == 0:
            # First line of a split body section in fileLines contains:
            # . file type 'split',
            # . folder name for CSV file.
            # Skip lines for other file types.
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
            fileType = entries[0]
            if fileType == 'split':
                splitFolder = create_folder(entries[1])
                li += 1
        elif li == 1:
            li += 1
            # Second line of a split body section in fileLines contains
            # info for split body filename
            entries = fLine.split(',')
            entries = [e.strip() for e in entries]
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
            # . Prepare for next split bodies section in fileLines
            li = 0
