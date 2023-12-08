FINCH TRACKER
## Description
Included are the following files
- DetectAruco_PiSide.py - primary file; handles live video processing and uploading aruco data to bigquery
- SetupConfig.py, SetupBirdConfig.py - handles setting config and displaying to GUI
- DetectAruco_PiSide.exe - DetectAruco_PiSide.py frozen with PyInstaller for easy execution
- config.json, birds_config.json - config files used by the py and exe; should be in same directory
- calib_img.png - used to calibrate the camera; should be in same directory as DetectAruco
- heatmap.py - generates animation for bird positions
- summaries.py [broken] - generates excel sheet summaries on bird activity

### GCloud BigQuery Project 
- Create new project
- Cick BigQuery
- Click on hotdog dots; click create dataset and name it
- Click Upgrade from free trial (and add billing info if not added and attach it to the project)
    - STREAM UPLOAD NOT ALLOWED IN FREE VERSION

### HOW TO USE
The executable files should be able to run on a Windows 10 machine from command line using .\[file.exe].
These do not require PyPi packages to be installed.

Gcloud CLI will need to be installed and authentication credentials set to save the data to bigquery.
    (An error will be thrown if this has not been done. It will contain a link to the gcloud CLI installation page
    as well as the commands necessary to set default authentication credentials. This may have to be done twice.)
The project id, dataset id, and table name can be set through the config GUI or in config.json.

! STREAM UPLOAD NOT ALLOWED IN FREE VERSION
- Upgrade and add billing (see above) 
- A new table must be created/used if one was created before adding billing

The python files will require the installation of python and several packages to run.
- The required modules will throw a ModuleNotFoundError and can usually be installed with 'pip install [module]'
- If not, the proper command is easily searchable from the specific error.
A py file can be run from the command line with 'python [file.py]'


### UNFINISHED
 - Actually getting the code running on the RPi
 - Some GUI update bugs (bird ids not updating) in SetupBirdConfig.py
 - Fix summaries.py
 - Make post-processing features accessible (heatmap, summaries) by GUI