# Scripts to create objects in Fusion360 from CSV files using the API

## 1. Overview
* API/libraries contains library files that are used in the other scripts for handling CSV files and Fusion360 objects.
* API/Scripts contains scripts that can run in Fusion360 to create objects like sketches, planes, lofts, bodies from CSV files.

## 2. API/libraries
* interfacefiles.py - functions to create separate CSV files from a text file.
* interface360.py - functions for user IO in the Fusion360 GUI.
* utilities360.py - functions for handling objects in Fusion360.
* schemacsv360.py - functions to represent items defined in CSV schema files in Fusion360.
* importsketch.py - import a sketch from a CSV file.
* createloft.py  - create a loft from sketch profiles and rails defined in a CSV file.
* createplane.py - create a plane from three points defined in a CSV file.
* splitbody.py - split body defined in a CSV file.
* combinebodies.py - combine bodies defined in a CSV file
* constructassembly.py - construct assembly defined in a CSV file, using sketches, planes, bodies

## 3. API/Scripts
The path to the API/Scripts directory needs to be set in Fusion360 via menu Preferences/General/API in the Fusion360 GUI.

### 3.1 Design scripts
* AssemblyCSV - Generic script to assemble a design in Fusion360 as defined in assembly CSV file. Using AssemblyCSV with csv/F35B-CSV.csv is equivalent to using the dedicated AssembleF35bCSV script.
* AssembleF35bCSV - Dedicated script to assemble F35B plane design in Fusion360 as defined in CSV files.

### 3.2 General scripts for processing one CSV file, or multiple CSV files
* ImportSketchCSV, ImportSketchesCSV - Import sketch as defined in CSV file.
* CreateLoftCSV, CreateLoftsCSV - Create loft as defined in CSV file.
* CreatePlaneCSV, CreatePlanesCSV - Create plane as defined in CSV file.
* SplitBodyCSV, SplitBodyMultipleCSV - Split body as defined in CSV file.
* CombineBodiesCSV, CombineBodiesMultipleCSV - Combine bodies as defined in CSV file.

### 3.3 Example scripts
### 3.3.1 Example script
The Example script demonstrates some script development basics in Fusion360 by printing component names in the TEXT COMMANDS window of Fusion360, as shown below.
![Print text in TEXT COMMANDS window in Fusion360](doc/print_text_v2.jpg)

#### 3.3.2 ImportSketchCSV and ImportSketchesCSV scripts with test/snail/snail_points.py
Demonstrate creating three sketch CSV files of a snail, in three different offset planes of the XY, YZ and ZX origin planes. First run 'python snail_points.py' on the command line in a terminal, to create separate CSV files in a csv/sketches folder from snail_points.txt. One CSV file can be read into Fusion360 using the ImportSketchCSV script, or all three CSV files can be read at once into Fusion360 using the ImportSketchesCSV script.
![Read sketches into Fusion360 from CSV files](doc/snail_3d_v2.jpg)

#### 3.3.3 AssemblyCSV script with F35B/f35b_points.py
The f35b_points.py creates CSV files from f35b_points.txt for a F35B plane fuselage and wing. First run 'python f35b_points.py' on the command line in a terminal, to create separate CSV files in a csv/ folder. The F35B design shown below, can then be generated in Fusion360 from these CSV files, by running the AssemblyCSV Script with the csv/F35B-CSV.csv file in the Fusion360 GUI (takes about 2 minutes).
![F35B created from CSV files](doc/f35b_csv.jpg)
