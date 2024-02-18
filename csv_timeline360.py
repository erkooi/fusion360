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

The csv_timeline360.py script uses a timeline txt file, that defines a design
in Fusion 360. The timeline txt file contains schema sections that define CSV
files for generating objects in Fusion360:

- Comment lines or comment in lines will be removed (comment = #)
- Schema sections start with an object keyword and end with an empty line.
- For each schema section a separate CSV file will be created in the
  specified sub directory.
- See f35b_points.txt for object schema section examples.
- See docstrings of libraries/ python files for schema definition per object.

Schema sections in point txt file:

. Object keyword: sketch, plane, loft, extrude, combine, split, movecopy,
  mirror.
  - interfacefiles.write_csv_files()

. Object keyword: sketch, cross_rails
  Create cross rail sketches CSV files. The sketch files can be used for
  profiles and cross rails to use with loft. For the sketch sections the
  segmentType can have optional cross_rail railName(s), that will not appear in
  the CSV file, but are used by interfacefiles.read_cross_rails_definitions()
  to include that segment point in a cross rail sketch. The cross rails are
  made between points with equal coordinate in different profile sketches.
  - interfacefiles.write_cross_rail_sketch_csv_file()

. Object keyword: sketch, co_rails
  Creat co rail sketches CSV files. The co-rails are derived from segmentType
  sections in a profile sketch that can have optional co_rail railName(s) that
  will not appear in the CSV file of the sketch, but are used by
  interfacefiles.determine_co_rail_sketch_csv_files() to include that segment
  in a co rail sketch.
  - interfacefikles.write_co_rail_sketch_csv_files()

. Object keyword: assembly
  Create assembly CSV files to define assemblies
  - interfacefiles.write_assembly_csv_file()

Usage of CSV files in Fusion360:
1) Manually: Select active component in Fusion360 GUI and then use script from
   Utilities/Add-Ins/Scripts to generate the objects, either for all CSV files
   in folder or for one specific CSV at a time. The active component is then
   the hostComponent.
2) Automatically: Use Script/AssemblyCSV script to load all necessary CSV files
   and use assembly CSV file to apply the CSV files in Fusion 360 in the
   correct order. The assemblyComponent is then the hostComponent for the
   groupComponents.

Usage on command line:
> python csv_timeline360.py -f f35b_points.txt
"""

import argparse
import interfacefiles
import userparameters


if __name__ == '__main__':
    # Parse arguments
    _parser = argparse.ArgumentParser('csv_timeline360')
    _parser.add_argument('-f', default='f35b_points.txt', type=str, help='Timeline file name')
    args = _parser.parse_args()
    timelineFilename = args.f

    # Read timeline file
    fileLines = interfacefiles.read_data_lines_from_file(timelineFilename)

    # Read units
    units = interfacefiles.read_units_from_file_lines(fileLines)

    # Process parameters
    parametersDict = userparameters.read_parameters_from_file_lines(fileLines)
    fileLines = userparameters.replace_parameters_in_file_lines(fileLines, parametersDict)

    # Write CSV files
    nofFiles = 0

    # Write plane CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'plane', units)

    # Write sketch CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'sketch', units)

    # Write co rail sketches CSV files for sketch segments with a co_rail name
    nofFiles += interfacefiles.write_co_rail_sketch_csv_files(fileLines, units)

    # Write cross rail sketches CSV files for points between profile sketches
    nofFiles += interfacefiles.write_cross_rail_sketch_csv_files(fileLines, units)

    # Write loft CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'loft')

    # Write extrude CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'extrude', units)

    # Write combine CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'combine')

    # Write split CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'split')

    # Write movecopy CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'movecopy', units)

    # Write mirror CSV files into folder(s)
    nofFiles += interfacefiles.write_csv_files(fileLines, 'mirror')

    # Write assembly CSV file
    nofFiles += interfacefiles.write_assembly_csv_file(fileLines)

    # Report
    print('Wrote total %d CSV files for %s' % (nofFiles, timelineFilename))

    userparameters.print_parameters_dict(parametersDict)
