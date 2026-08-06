## Running the Server

To start the UIL Forces server, run the executable file provided, either by simply double-clicking it or running it through a console window. Then, follow the instructions under [Judge System Setup](#judge-system-setup) and [Database Setup](#database-setup).

## Judge System Setup

If you install UIL Forces from the provided [Windows release](https://github.com/tvumcc/uil-forces/releases), the tools need to grade Java and Python submissions will be packaged in the `tools` directory. If these need to be changed, you can replace them with different versions. The judge scans `tools` for `python.exe` (for Python) and `javac.exe` and `java.exe` (for Java). (Windows Only)

If the judge cannot find a specific program in the `tools` directory, it falls back to using the programs `python`, `javac`, or `java` respectively, if they are on the PATH environment variable.

### Judge System Testing

Run action 3: "Judge: Check required tools", to make sure that the judge system can access the necessary Java and Python toolchains for grading user submissions.

If those succeed, then run action 4: "Judge: Test grading system". This will try submitting code to the judge system to make sure that setup is complete.

## Database Setup

Setup only needs to be done once for each instance of UIL Forces. It is done to initialize the database with all of the problem sets, PDFs, and data files.

Before setup, make sure to add a secret key (any form of text) in a file called `secret.txt` located in the root directory. This directory will also contain the database file which will be created after going through the following steps.

After running UIL Forces, select action 2: "Start server setup". This will scan the working directory for a folder named `setup` with a file structure as specified in [Setup Folder Structure](#setup-folder-structure)

Once setup is complete, you will not have to mess with problem sets unless new problems need to be added. This can be done either through the admin panel, or by editing the setup folder and config file to add the new problem set. If new problem sets are added to the setup folder, rerun the "Start server setup" action and the interface will allow the new problem sets to merge into the current database, without ever removing any existing problem sets.

## Usage

After a database has been initialized with problem sets and an admin user, most usage will involve creating contests through the admin panel and adding problem sets (which can be from different problem sets).

## Logs

Logs throughout the lifetime of a UIL Forces instance are stored in the `logs` folder of the root directory.

## Backups

Before and after each contest, it would be wise to copy `main.db` to a separate location (USB drive, cloud
folder). This file contains all users, submissions, and scores, so losing it means losing
contest history permanently.

## Setup Folder Structure

This is how the setup folder should be set up so that UIL Forces can read it correctly:


<p align="center"><img src="screenshots/setup_file_structure.png"></p>

- `pdfs`: A directory containing the PDFs (programming packets) that each problem set will reference.
- `psets`: A directory containing the input and output data for each problem set. As shown in the picture below, each problem set has its own directory. At the root of this directory is the judge data and in the nested `student_data` directory is the student data. The data file names in `student_data` should be the same as their judge data counterparts.  

<p align="center"><img src="screenshots/psets_file_structure.png"></p>

- `setup.yaml`: This is the configuration file used to match PDFs and data files to their respective problem sets and initialize settings and users. It is mainly used to make an admin user since at least one admin user must be created at setup in order to access the admin panel (from which you can create more users with or without admin privileges if needed).
  - Data files will automatically be detected based on UIL's usual convention that the data file names are the lowercased version of the problem name. For exceptions to this rule, use the YAML keys `input_data_file` and `output_data_file` to specify actual data file names.
  - The `pages` YAML key specifies which page numbers (space separated) of the problem set PDF should be loaded when the problem is selected on the submission page.

An example of a valid setup directory can be found in `backend/setup-example`. Note that this folder must be renamed to `setup` and be placed in the same directory as the project executable file.