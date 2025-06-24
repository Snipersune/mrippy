# Brain MRI Preprocessing Pipeline
The main purpose of this python script is to perform DICOM to nifti conversion. By default, ACPC aligment and bias field correction (bfc) are also performed. The processing order is: 'dcm2nii->acpc->bfc', but any of the steps can be skipped through the use of command line flags (described in the 'How to use' section).

## Setup process
To setup the script, Python (version 3.7 >) must be installed on the machine and ```python3``` must be in the system path. To check if this is the case, open a terminal window and run the following command: ```python3 --version```. If the command returns some python version, everything should be okey. If the output is 'command not found: python3', Python is not installed on the machine.

Assuming python is installed correctly, the setup procedure is as follows: 

- Open a terminal window and go to the directory where the script is located.
- Enter the command ```./setup.sh```. This will create a virtual environment 'venv' with the required python packages.
- Activate the virtual environment with the command ```source venv/bin/activate```. The leftmost text in the terminal promts should now have changed to '(venv)'.

If the following steps could be followed without errors, the script is ready to use.


## How to use
To use the script, open a terminal and make sure you move to the directory where the script is located. If the virtual environment is not active, enter ```source venv/bin/activate``` to activate it.

The baseline usage of the script is of the form ```python3 pipeline.py -i <INPUT_DIR> -o <OUTPUT_DIR>```, where ```<INPUT_DIR>``` and  ```<OUTPUT_DIR>``` are the absolute or relative paths of the input and output directories respectively. This will perform the default processing steps as mentioned above ('dcm2nii->acpc->bfc'). 

Below are the flags recognized by the script, some of which can be used to skip desired processing steps.

### Flags

- -i, --inDir - Directory of input data to perform actions on. (required)
- -o, --outDir - Directory to save output data into. (required)
- -z, --doZip - Save output nifti files in compressed format '.gz'.
- --do - Specify which processing steps to do. Possible options are:
  - 'n' - dcm to nifti conversion.
  - 'b' - Bias field correction.
  - 'a' - ACPC alignment.\
Default option is 'n'. Multiple steps can be specified by writing a sequence of options, e.g. 'nab', where the steps are performed in the order of the string.
- --decap - ```--decap <fac>``` will 'decapitate' volume by setting bottom ```<fac>``` percent of slices to 0 and shift the remaining volume down by half the amount removed to center it. Is performed prior to ACPC alignment.
- --bfcFac - Shrink factor for bias field correction. Computes correction on a lower resolution image shrunken by <bfcFac> in all directions to reduce computational load and increased speed, at the expense of accuracy. Deafult is 4.

### Errors and 
sudo apt-get install libatlas3-base









