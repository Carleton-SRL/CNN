# Introduction

The Collaborative Neuromorphic Nerds (or CNN for short) is a repository focused on using event cameras (or Neuromorphic cameras) for spacecraft proximity operations research. The Nerds consist of three researchers at Carleton University, one PhD Candidate and two MASc students, each focusing on different areas of research but all united in one goal: developing a robust pipeline to take event camera measurements and transform them into useful ouputs.

# Navigation

This README will be updated as the repository is developed, but for the moment the repository will only contain simple code to records and manipulate event data collected within the Spacecraft Robotics Laboratory.

## Import Folder

The ['import'](https://github.com/Carleton-SRL/CNN/tree/main/import) folder in the repository contains Python code to import the AEDAT4 data into an HDF5 dataset or a MAT dataset. There are two scripts which are named according to their purpose. 

> [!CAUTION]
> The code that imports the data into a MAT file is currently only useful for smaller event datasets. For larger datasets, this code can quickly crash your computer. It is generally better to use the HDF5 converter, as HDF5 is supported in both MATLAB and Python.
