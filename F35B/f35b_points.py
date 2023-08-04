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
# Author: Eric Kooistra
# Date: 25 Mar 2023
"""Create separate CSV files from design coordinates defined in a txt file.

The script is design file specific and uses f35b_points.txt, that defines the
entire design for a F35B plane fuselage and wings.

The txt file contains schema sections that define CSV files for generating
objects in Fusion360.
- Comment lines or comment in lines will be removed (comment = #)
- Schema sections start with an object keyword and end with an empty line.
- For each schema section a separate CSV file will be created in the
  specified sub directory.
- See f35b_points.txt for object schema section examples.
- See docstrings of libraries/ python files for schema definition per object.

Schema sections in txt file:

. Object keyword: sketch
  Create sketch CSV files. The sketch files can be used for profiles and rails
  to use with loft. For the sketch sections the segmentType can have optional
  railName(s), that will not appear in the CSV file, but are used by
  interfacefiles.get_rail_points() to include that segment point in a rail
  sketch. The rails are made between points with equal coordinate in different
  profile sketches.
  - interfacefiles.write_profile_sketch_files
  - interfacefiles.get_rail_points() -->
    interfacefiles.write_rail_sketch_file()

. Object keyword: loft
  Create loft CSV files to use with loft.
  - interfacefiles.write_loft_files()

. Object keyword: plane
  Create plane CSV files to use as split plane
  - interfacefiles.write_plane_files()

. Object keyword: combine
  Create combine bodies CSV files to use with combine bodies
  - interfacefiles.write_combine_bodies_files()

. Object keyword: split
  Create split body CSV files to use with split body
  - interfacefiles.write_split_body_files()

Usage of CSV files in Fusion360:
1) Manually: select active component in Fusion360 GUI and then use Script
   to generate the objects, either for all CSV files in folder or for one
   specific CSV at a time.
2) Automatically: run dedicated Script that generates all necessary objects
   and applies the CSV files in the correct order. Use the AssembleF35bCSV
   script to create the F35B plane of picture doc/f35b_csv.jpg in Fusion360.

Usage on command line:
> python f35b_points.py
"""

import os
import os.path
import interfacefiles


if __name__ == '__main__':
    units = 'mm'
    pointsFilename = 'f35b_points.txt'
    yRailsFolder = interfacefiles.create_folder(os.path.join('csv', 'sketches_rails_y'))
    yRails = [0, -63, -75, -90, -98, -112, -123, -138, -154, -175, -213, -250]

    yRailsCutFolder = interfacefiles.create_folder(os.path.join('csv', 'sketches_cut_rails_y'))
    yRailsCut = [0, -63, -75, -90, -98, -112, -123, -138, -154, -175, -213, -225, -250]

    zRailsFolder = interfacefiles.create_folder(os.path.join('csv', 'sketches_rails_z'))
    zRails = [19]

    zRailsCutFolder = interfacefiles.create_folder(os.path.join('csv', 'sketches_cut_rails_z'))
    zRailsCut = [0, 19]

    # Read points file for the planes, sketches and lofts
    fileLines = interfacefiles.read_data_lines_from_file(pointsFilename)

    # Write plane csv files into folder(s)
    interfacefiles.write_plane_files(fileLines)

    # Write profile sketch csv files into folder(s)
    interfacefiles.write_profile_sketch_files(fileLines)

    # Get rail points for y rail sketches
    for y in yRails:
        railNames = ['top', 'bottom']
        for railName in railNames:
            railPoints = interfacefiles.get_rail_points(fileLines, 'x', railName, 'y', y)
            filename = 'y_' + str(abs(y)) + '_' + railName + '.csv'
            filename = os.path.join(yRailsFolder, filename)
            interfacefiles.write_rail_sketch_file('y', y, 'spline', railPoints, filename)
            # print('y', y, railName, railPoints)
        # print('')

    # Get rail points for z rail sketches
    for z in zRails:
        railNames = ['edge_point', 'edge_inlet', 'edge_bin', 'edge_wing']
        for railName in railNames:
            railPoints = interfacefiles.get_rail_points(fileLines, 'x', railName, 'z', z)
            filename = 'z_' + str(abs(z)) + '_' + railName + '.csv'
            filename = os.path.join(zRailsFolder, filename)
            interfacefiles.write_rail_sketch_file('z', z, 'spline', railPoints, filename)
            # print('z', z, railPoints)
        # print('')

    # Get rail points for cut_y rail sketches
    for y in yRailsCut:
        railNames = ['cut_top', 'cut_bottom']
        for railName in railNames:
            railPoints = interfacefiles.get_rail_points(fileLines, 'x', railName, 'y', y)
            filename = 'cut_y_' + str(abs(y)) + '_' + railName + '.csv'
            filename = os.path.join(yRailsCutFolder, filename)
            interfacefiles.write_rail_sketch_file('y', y, 'spline', railPoints, filename)
            # print('y', y, railName, railPoints)
        # print('')

    # Get rail points for z rail sketches
    for z in zRailsCut:
        railNames = ['cut_edge_nose', 'cut_edge_inlet', 'cut_edge_bin', 'cut_edge_wing', 'cut_edge_chord',
                     'cut_edge_bin_end']
        for railName in railNames:
            railPoints = interfacefiles.get_rail_points(fileLines, 'x', railName, 'z', z)
            filename = 'cut_z_' + str(abs(z)) + '_' + railName + '.csv'
            filename = os.path.join(zRailsCutFolder, filename)
            interfacefiles.write_rail_sketch_file('z', z, 'spline', railPoints, filename)
            # print('z', z, railPoints)
        # print('')

    # Write loft csv files into folder(s)
    interfacefiles.write_loft_files(fileLines)

    # Write combine bodies csv files into folder(s)
    interfacefiles.write_combine_bodies_files(fileLines)

    # Write split body csv files into folder(s)
    interfacefiles.write_split_body_files(fileLines)
