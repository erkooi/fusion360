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

The csv_points360.py script uses a points txt file, that defines a design in
Fusion 360. The points txt file contains schema sections that define CSV files
for generating objects in Fusion360:

- Comment lines or comment in lines will be removed (comment = #)
- Schema sections start with an object keyword and end with an empty line.
- For each schema section a separate CSV file will be created in the
  specified sub directory.
- See f35b_points.txt for object schema section examples.
- See docstrings of libraries/ python files for schema definition per object.

Schema sections in point txt file:

. Object keyword: sketch
  Create sketch CSV files. The sketch files can be used for profiles and rails
  to use with loft. For the sketch sections the segmentType can have optional
  railName(s), that will not appear in the CSV file, but are used by
  interfacefiles.get_cross_rail_points() to include that segment point in a rail
  sketch. The rails are made between points with equal coordinate in different
  profile sketches.
  - interfacefiles.write_profile_sketch_files()
  - interfacefikles.write_co_rail_sketch_files()
  - interfacefiles.write_cross_rail_points_sketch_files()

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

. Object keyword: movecopy
  Create movecopy CSV files to use with move, copy, translate component or body
  - interfacefiles.write_movecopy_files()

. Object keyword: assembly
  Create assembly CSV files to define assemblies
  - interfacefiles.write_assembly_files()

Usage of CSV files in Fusion360:
1) Manually: Select active component in Fusion360 GUI and then use script from
   Utilities/Add-Ins/Scripts to generate the objects, either for all CSV files
   in folder or for one specific CSV at a time.
2) Automatically: Use Script/AssemblyCSV script to load all necessary CSV files
   and use assembly CSV file to apply the CSV files in Fusion 360 in the
   correct order.

Usage on command line:
> python csv_points360.py -f f35b_points.txt
"""

import argparse
import interfacefiles


if __name__ == '__main__':
    # Parse arguments
    _parser = argparse.ArgumentParser('csv_points360')
    _parser.add_argument('-f', default='f35b_points.txt', type=str, help='Points file name')
    args = _parser.parse_args()
    pointsFilename = args.f

    # Read points file for the planes, sketches, lofts, combine, etc
    fileLines = interfacefiles.read_data_lines_from_file(pointsFilename)

    # Write csv files
    nofFiles = 0

    # Write plane csv files into folder(s)
    nofFiles += interfacefiles.write_plane_files(fileLines)

    # Write profile sketch csv files into folder(s)
    nofFiles += interfacefiles.write_profile_sketch_files(fileLines)

    # Write co rail sketches for sketch segments with a co_rail name
    nofFiles += interfacefiles.write_co_rail_sketch_files(fileLines)

    # Write cross rail sketches for points between profile sketches
    nofFiles += interfacefiles.write_cross_rail_points_sketch_files(fileLines)

    # Write loft csv files into folder(s)
    nofFiles += interfacefiles.write_loft_files(fileLines)

    # Write extrude csv files into folder(s)
    nofFiles += interfacefiles.write_extrude_files(fileLines)

    # Write combine bodies csv files into folder(s)
    nofFiles += interfacefiles.write_combine_bodies_files(fileLines)

    # Write split body csv files into folder(s)
    nofFiles += interfacefiles.write_split_body_files(fileLines)

    # Write movecopy csv files into folder(s)
    nofFiles += interfacefiles.write_movecopy_files(fileLines)

    # Write assembly csv files into folder(s)
    nofFiles += interfacefiles.write_assembly_files(fileLines)

    # Report
    print('Wrote total %d csv files for %s' % (nofFiles, pointsFilename))
