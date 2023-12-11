FINCH TRACKER
## Description
Included are the following files
- DetectAruco_PiSide.py - primary file; handles live video processing and uploading aruco data to bigquery
- SetupConfig.py, SetupBirdConfig.py - handles setting config and displaying to GUI
- DetectAruco_PiSide.exe - DetectAruco_PiSide.py frozen with PyInstaller for easy execution
- config.json, birds_config.json - config files used by the py and exe; should be in same directory
- calib_img.png - used to calibrate the camera; should be in same directory as DetectAruco
- heatmap.py - generates animation for bird positions
- PostProcessing.py - generates heatmap(s) of bigq table data
- PostProcessing.exe - PostProcessing.py frozen
- summaries.py [broken] - generates excel sheet summaries on bird activity

### GCloud BigQuery Project 
#GCLOUD CLI FOR AUTHENTICATION
Gcloud CLI will need to be installed and authentication credentials set to save the data to bigquery.
    (An error will be thrown if this has not been done. It will contain a link to the gcloud CLI installation page
    as well as the commands necessary to set default authentication credentials. This may have to be done twice.)
    - Download GoogleCloud CLI
    - Open and enter command 'gcloud auth application-default login' the login
The project id, dataset id, and table name can be set through the config GUI or in config.json.

# GCLOUD PROJECTS ACCOUNT
- Click the blue 'Start free' and click through
- Enter card data
    ! Billing must be added to stream data; If a table was created before billing added, a new table must be used for this

# CREATING A PROJECT
- Click My First Project -> New project; Name the project
- Select your created project
- Click lefthand hamburger button -> BigQuery; Enable API if prompted
- Next to your project name click the hotdog button -> Create dataset; Create a dataset

#UPDATING CONFIG
- Open config.json in a text editor or run DetectAruco_PiSide.exe to set project id, dataset id to current; set table_name to desired
 - ( table_name can be changed to create a different table under the same project and dataset )

### HOW TO USE
#Executables
The executable files should be able to run on a Windows 10 machine from command line using .\[file.exe] or by double-clicking
These do not require PyPi packages to be installed.
To stop execution from command line, press ctrl+c 
- If data is uploaded successfully, there should be a line stating 'Data uploaded to'...

#Python File
The python files will require the installation of python and several packages to run.
- The required modules will throw a ModuleNotFoundError and can usually be installed with 'pip install [module]'
- If not, the proper command is easily searchable from the specific error.
A py file can be run from the command line with 'python [file.py]'

#Testing Upload
- On the Gcloud projects Bigquery page, go to your table by clicking on your project->dataset->table
Opt 1: Click the preview tab to see if any data is making it to the table
Opt 2: Click Query tab, open a new query, and run this command (table id should be generated for you):
        SELECT * FROM `[your_project].[your_dataset].[your_table]` 
        ORDER BY timestamp DESC
        LIMIT 1000
    - The above command will display the top 1000 most recent rows
