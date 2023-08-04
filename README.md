# Scripts to create objects in Fusion360 from CSV files using the API

## Overview
* API/libraries contains library files that are used in the other scripts for handling CSV files and Fusion360 objects.
* API/Scripts contains scripts that can run in Fusion360 to create objects like sketches, planes, lofts, bodies from CSV files.
* F35B/ contains a design specific script f35b_points.py, that creates CSV files for F35B plane fuselage and wing. First run 'python f35b_points.py' on the command line in a terminal. The F35B design shown below, can then be generated in Fusion360 from these CSV files, by running the AssembleF35bCSV Script in the Fusion360 GUI.
![F35B created from CSV files](doc/f35b_csv.jpg)
   
## API/libraries
* interfacefiles.py - functions to create separate CSV files from a text file.
* interface360.py - functions for user IO in the Fusion360 GUI.
* utilities360.py - functions for handling objects in Fusion360.
* schemacsv360.py - functions to represent items defined in CSV schema files in Fusion360.
* importsketch.py - import a sketch from a CSV file.
* createloft.py  - create a loft from sketch profiles and rails defined in a CSV file.
* createplane.py - create a plane from three points defined in a CSV file.
* splitbody.py - split body defined in a CSV file.
* combinebodies.py - combine bodies defined in a CSV file

## API/Scripts
The path to the API/Scripts directory needs to be set in Fusion360 via menu Preferences/General/API in the Fusion360 GUI.

### Example scripts
* Example/ - Demonstrate some script development basics in Fusion360 by printing component names, as shown below.
![Print text in TEXT COMMANDS window in Fusion360](doc/print_text_v2.jpg)

### Design scripts
* AssembleF35bCSV/ - Assemble F35B plane design in Fusion360 as defined in CSV files.

### General scripts for processing one CSV file, or multiple CSV files
* ImportSketchCSV/, ImportSketchesCSV/ - Import sketch as defined in CSV file.
* CreateLoftCSV/, CreateLoftsCSV - Create loft as defined in CSV file.
* CreatePlaneCSV/, CreatePlanesCSV - Create plane as defined in CSV file.
* SplitBodyCSV/, SplitBodyMultipleCSV - Split body as defined in CSV file.
* CombineBodiesCSV, CombineBodiesMultipleCSV/ - Combine bodies as defined in CSV file.
