# Scripts to create objects in Fusion360 from CSV files using the API
* API/libraries contains library files that are used in the Scripts
* API/Scripts contains scripts that can run in Fusion360

## API/libraries
* interfacefiles.py - functions to create separate CSV files from a text file
* interface360.py - functions for user IO in the Fusion360 GUI
* utilities360.py - functions for handling objects in Fusion360
* schemacsv360.py - functions to represent items defined in CSV schema files in Fusion360
* importsketch.py - import a sketch from a CSV file
* createloft.py  - create a loft from sketch profiles and rails defined in a CSV file
* createplane.py - create a plane from three points defined in a CSV file
* splitbody.py - split body defined in a CSV file
* combinebodies.py - combine bodies defined in a CSV file

## API/Scripts
### Example scripts
* Example/ - demonstrate some script development basics Fusion360

### Design specific scripts
AssembleF35bCSV/ - Assemble F35B plane design in Fusion360 as defined in CSV files

### General scripts for processing one CSV file
* ImportSketchCSV - Import sketch as defined in CSV file
* CreateLoftCSV/ - Create loft as defined in CSV file
* CreatePlaneCSV/ - Create plane as defined in CSV file
* SplitBodyCSV/ - Split body as defined in CSV file
* CombineBodiesCSV/ - Combine bodies as defined in CSV file

### General scripts for processing multiple CSV files in a folder
* ImportSketchesCSV/
* CreateLoftsCSV
* CreatePlanesCSV/
* SplitBodyMultipleCSV/
* CombineBodiesMultipleCSV/
