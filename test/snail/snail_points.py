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
# Date: 19 Aug 2023
"""Create separate CSV files from design coordinates defined in a txt file.

The script is design file specific and uses snail_points.txt, that defines
three sketches of a snail, each on another origine offset plane.

Usage on command line:
> python snail_points.py

Or use the general csv_points360.py script to create the CSV files for the
design:
> python ../../csv_points360.py -f snail_points.txt
"""

import interfacefiles


if __name__ == '__main__':
    pointsFilename = 'snail_points.txt'

    # Read points file
    fileLines = interfacefiles.read_data_lines_from_file(pointsFilename)

    # Write sketch csv files into folder
    interfacefiles.write_profile_sketch_files(fileLines)
