# RE/MAPS Real Estate
<div class="markdown-heading"><a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" data-canonical src="https://img.shields.io/badge/License-MIT-yellow.svg" style="max-width: 100%;"></a></div>
A python script for GIS to locate unknown point/multipoint(s) place held (0 0)/(EMPTY) in Well Known Text (WKT) to within the boundary of a user defined polygon. Creates new csv and layer saved to location of user’s choosing. 

> [!NOTE]
> (0 0) can be any WKT, (0 0) is just my placeholder for **reasons** and works for me.<br>
> There are three references to it that can be easily altered, removed, or left alone to suit your own needs.

Run from QGIS python console plugin.
***
## Why?
I had a situation where I needed to map a cpl/few hundred property related files. Each file could contain between one and many (continuous or not) properties. Apx 10% of all the properties’ locations are lost/unknown (to date). I needed to see a representation of all the data in the general ‘neighborhood’ of the region and be able to interact with it: to view associated data despite not having the exact location of some of it. That is, I needed to be able to click on a marker, and get the associated csv row’s info as well as see all related properties from the parent file.
***
## Process:
I added a column in the table converting lat-lon coordinates to multipoint WKT, this has the added benefit of associating many property point locations with the single csv row (file). However, (0 0) points map inappropriately far off from where they needed to be. Additionally, I also don’t want the points stacked and if an unknown is associated with a known aka in the same row of the csv moving one moves the other(s).

First, I added the table as delimited text layer. To solve the (0 0) mapping issue I created a new shapefile layer and added a polygon in a known empty region near the rest of the properties. I then used ChatGPT and my tiny knowledge of python to write a script that duplicates the source file and edits strings in the WKT column to replace (0 0)/(EMPTY) with random points generated from within the polygon boundary. Essentially having ‘remapped’ them, the shapefile layer can now also be used to distinguish that “properties” within it’s confine are only representationally located in that physical area and that they are actually “unknown.” Lots of fun ways to visually represent the distinction between the two layers at this point.
***
## How to in QGIS:
### Step 1. 
Git clone / download this repository
### Step 2. 
Open the Python console in QGIS
### Step 3. 
In the [console code editor](https://docs.qgis.org/3.28/en/docs/user_manual/plugins/python_console.html#the-code-editor) run:
```python
exec(open(r"/PATH_TO_FILE/RE-MAPS_Real_Estate.py".encode('utf-8')).read())
```
I’m using linux, if in Windows it’ll look something like:
```python
exec(open(r"C:\PATH_TO_FILE\RE-MAPS_Real_Estate.py".encode('utf-8')).read())
```
*If run from the the processing toolbox as existing script it will kick a not a valid [processing script error](https://docs.qgis.org/3.28/en/docs/user_manual/processing/scripts.html) on completion.*
### Step 3 (*alternate*).
Just open the editor from the console and paste in the code then click the **Run Script** button to execute.
### Step 4.
Save your work.


