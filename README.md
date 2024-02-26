# Scripts to create objects in Fusion360 from CSV files using the API

For more information please also check my channel "Eric Kooistra - Hobby" on YouTube: https://www.youtube.com/channel/UCnQhySYKmPyZsY2G8S3CUbA

## 1. Overview
* API/libraries contains library files that are used in the other scripts for handling CSV files and Fusion360 objects.
* API/Scripts contains scripts that can run in Fusion360 to create objects like sketches, planes, lofts, bodies from CSV files.

## 2. API/libraries
Functions to converting an assembly timeline file into separate CSV files:
* interfacefiles.py - functions to create separate CSV files from a text file.
* userparameters.py - functions process parameters in a timeline file.

Functions to ease using the Fusion360 API:
* schemacsv360.py - functions to represent items defined in CSV schema files in Fusion360.
* interface360.py - functions for user IO in the Fusion360 GUI.
* utilities360.py - functions for handling objects in Fusion360.
* samples360.py - functions for example samples to experiment with the API in Fusion360.

Functions to parse and excecute action CSV files in Fusion360:
* importsketch.py - import a sketch from a CSV file.
* createplane.py - create a plane from three points defined in a CSV file.
* createloft.py  - create a loft from sketch profiles and rails defined in a CSV file.
* combinebodies.py - combine bodies defined in a CSV file
* extrude.py  - extrude sketch profile defined in a CSV file.
* splitbody.py - split body defined in a CSV file.
* movecopy.py - move, copy, transfer operation defined in a CSV file.
* mirror.py - mirror body or component defined in a CSV file.
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
* MoveCopyCSV - Perform move, copy operation as defined in CSV file.

### 3.3 Example scripts
### 3.3.1 Example script
The Example script demonstrates some script development basics in Fusion360 by printing parameter values and object names in the TEXT COMMANDS window of Fusion360, as shown below.

![Print text in TEXT COMMANDS window in Fusion360](doc/print_text_v2.jpg)

#### 3.3.2 ImportSketchCSV and ImportSketchesCSV scripts with csv_timeline360.py
The snail_points.txt file defines three sketches of a snail in Fusion360. The three sketches are made in different offset planes of the XY, YZ and ZX origin planes. First in test/snail run 'python ../../csv_timeline360.py -f snail_points.txt' on the command line in a terminal, to create separate CSV files in a csv/sketches folder from snail_points.txt. One CSV file can be read into Fusion360 using the ImportSketchCSV script, or all three CSV files can be read at once into Fusion360 using the ImportSketchesCSV script.

![Read sketches into Fusion360 from CSV files](doc/snail_3d_v2.jpg)

#### 3.3.3 AssemblyCSV script with csv_timeline360.py
The csv_timeline360.py creates CSV files from F35B/f35b_points.txt for a F35B plane fuselage and wing. First in F35B/ run 'python ../csv_timeline360.py -f f35b_points.txt' on the command line in a terminal, to create separate CSV files in a csv/ folder. The F35B design in the F35B-CSV assembly component shown below, can then be generated in Fusion360 from these CSV files, by running the AssemblyCSV Script with the csv/F35B-CSV/F35B-points.csv file in the Fusion360 GUI (takes about 2 minutes).

![F35B created from CSV files](doc/f35b_csv.jpg)

Additional timeline actions for the F35B-CSV assembly component are defined in f35b-pin-holes.txt and f35b-aileron.txt. First create F35B-pin-holes.csv and F35B-aileron.csv using csv_timeline360.py on the command line in a terminal. After that the AssemblyCSV Script in Fusion360 can be used to perform the additional timeline actions defined in the assembly CSV files F35B-pin-holes.csv and in F35B-aileron.csv.

## 4 Directory (folder) tree of CSV files
The CSV files are organised in two folder levels:
* The CSV file for an assembly defines the assembly folder. The assembly folder can contain one or more assembly CSV files, that in series form a sequence of timeline actions, that together form the entire timeline for that assembly in Fusion360.
* The CSV files for timeline actions that belong to the assembly and that belong together are grouped in group folders. The group folder can be the same folder as the assembly folder, or a sub folder within the assembly folder.

Example of an directory tree for CSV files that together define an assmbly in Fusion360:
```
    assembly folder/group folder a/action csv files
                    group folder b/action csv files
                    group folder ...
                    assembly csv file 0
                    assembly csv file 1
                    assembly csv file ...
```

## 5 Fusion360 objects

### 5.1 Component and occurrence
An occurrence is like an instance of a component. There can be one or more occurrences of a component. The place in design hierarchy of a new component also is its first occurrence. For the root component there is no occurrence, because there can only be one root component.
* The root component can not be moved or copied.
* Component names are unique in the design.
* The CSV actions only create new components, therefore there is always only one occurrence of each component.

### 5.2 Sketch, plane, body
Sketches, planes and bodies have an unique name within a component, but can have the same name in different components. Therefor if a component is copied or mirrored, then there will be duplicate sketch, plane and bodies names in a design.


## 6 Hierarchy in Fusion360

### 6.1 Two levels
The assembly consist of an assemblyComponent and groupComponents. For an assembly the assemblyComponent is placed under the activeComponent. If the assemblyComponentName is not specified, then it defaults to the activeComponent. The activeComponent is the component in Fusion360 that is active when the AssemblyCSV script it ran.
* The assemblyComponent is used as hostComponent for the groupComponents. The results of a timeline action are placed in the groupComponent. If the groupComponent is used, then the groupComponentName should be the same as the group folder name in the directory tree. If the groupComponentName is not specified, then the group result objects will be placed in the assemblyComponent.
* A groupComponent contains the result objects of one or more timeline actions that belong together.

### 6.2 Multiple levels
To have more hierarchical freedom than the two level scope of assemblyComponent/groupComponent, it is also possible to define a component hierarchy for the assemblyComponent, for the groupComponent and to specify the component for input and target objects:
* assemblyComponentName = 'a/b/c' will use component 'a' as top level assembly component, 'b' as some intermediate level assembly and 'c' as sub assembly compoment. It will also create component hierarchy, if it does not already exist in the design in Fusion360.
* groupComponentName = 'd/e' will use component 'e' as groupComponent, but will also create intermediate component 'd' if necessary, to achieve component hierarchy activeComponent/a/b/c/d/e in Fusion360.

### 6.3 Input object search
Input objects, like sketch, plane, body, for timeline actions can be found by their 'object name' or by combination of 'parent component name/object name':
* If a timeline action depends on other objects, then it looks anywhere in the assemblyComponent to find objects that it has to operate on. In this way it can also find objects that are placed in other groupComponents within the assemblyComponent. The objects then must have a object name that is unique in the hostComponent and in all its child components.
* Alternatively input and target object names can be identified uniquely in the entire design by using their parent component name as well, because all component names are unique in a Fusion360 design. The object name 'd/object name' then uniquely identifies the object with that object name in component 'd'.
