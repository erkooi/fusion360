# Scripts to create objects in Fusion360 from CSV files using the API

For more information please also check my channel "Eric Kooistra - Hobby" on YouTube: https://www.youtube.com/channel/UCnQhySYKmPyZsY2G8S3CUbA

## 1. Overview
* API/libraries contains library files that are used in the other scripts for handling CSV files and Fusion360 objects.
* API/Scripts contains scripts that can run in Fusion360 to create objects like sketches, planes, lofts, bodies from CSV files.

## 2. API/libraries
* interfacefiles.py - functions to create separate CSV files from a text file.
* userparameters.py - functions process parameters in a timeline file.
* interface360.py - functions for user IO in the Fusion360 GUI.
* utilities360.py - functions for handling objects in Fusion360.
* schemacsv360.py - functions to represent items defined in CSV schema files in Fusion360.
* importsketch.py - import a sketch from a CSV file.
* extrude.py  - extrude sketch profile defined in a CSV file.
* createloft.py  - create a loft from sketch profiles and rails defined in a CSV file.
* createplane.py - create a plane from three points defined in a CSV file.
* movecopy.py - move, copy, transfer operation defined in a CSV file.
* splitbody.py - split body defined in a CSV file.
* combinebodies.py - combine bodies defined in a CSV file
* constructassembly.py - construct assembly defined in a CSV file, using sketches, planes, bodies

## 3. API/Scripts
The path to the API/Scripts directory needs to be set in Fusion360 via menu Preferences/General/API in the Fusion360 GUI.

### 3.1 Design scripts
* AssemblyCSV - Generic script to assemble a design in Fusion360 as defined in an assembly CSV file.

### 3.2 General scripts for processing one CSV file, or multiple CSV files
* ImportSketchCSV, ImportSketchesCSV - Import sketch as defined in CSV file.
* ExtrudeCSV, ExtrudesCSV - Extrude sketch profile as defined in CSV file.
* CreateLoftCSV, CreateLoftsCSV - Create loft as defined in CSV file.
* CreatePlaneCSV, CreatePlanesCSV - Create plane as defined in CSV file.
* SplitBodyCSV, SplitBodyMultipleCSV - Split body as defined in CSV file.
* CombineBodiesCSV, CombineBodiesMultipleCSV - Combine bodies as defined in CSV file.

### 3.3 Example scripts
### 3.3.1 Example script
The Example script demonstrates some script development basics in Fusion360 by printing component names in the TEXT COMMANDS window of Fusion360, as shown below.
![Print text in TEXT COMMANDS window in Fusion360](doc/print_text_v2.jpg)

#### 3.3.2 ImportSketchCSV and ImportSketchesCSV scripts with test/snail/snail_points.py
Demonstrate creating three sketch CSV files of a snail, in three different offset planes of the XY, YZ and ZX origin planes. First in test/snail run 'python ../../csv_timeline360.py -f snail_points.txt' on the command line in a terminal, to create separate CSV files in a csv/sketches folder from snail_points.txt. One CSV file can be read into Fusion360 using the ImportSketchCSV script, or all three CSV files can be read at once into Fusion360 using the ImportSketchesCSV script.

![Read sketches into Fusion360 from CSV files](doc/snail_3d_v2.jpg)

#### 3.3.3 AssemblyCSV script with csv_timeline360.py
The csv_timeline360.py creates CSV files from F35B/f35b_points.txt for a F35B plane fuselage and wing. First in F35B/ run 'python ../csv_timeline360.py -f f35b_points.txt' on the command line in a terminal, to create separate CSV files in a csv/ folder. The F35B design in the F35B-CSV assembly component shown below, can then be generated in Fusion360 from these CSV files, by running the AssemblyCSV Script with the csv/F35B-CSV/F35B-points.csv file in the Fusion360 GUI (takes about 2 minutes).

![F35B created from CSV files](doc/f35b_csv.jpg)

Additional timeline actions for the F35B-CSV assembly component are defined in f35b-pin-holes.txt and f35b-aileron.txt. First create F35B-pin-holes.csv and F35B-aileron.csv using csv_timeline360.py on the command line in a terminal. After that the AssemblyCSV Script in Fusion360 can be used to perform the additional timeline actions defined in F35B-pin-holes.csv and in F35B-aileron.csv.


