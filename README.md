# Visual Tour 3D Dubins
A Dubins Airplane equipped with a gimbaled camera flies through an urban environment represented as 2.5D objects to inspect a series of targets. The minimum time path that inspects the targets and returns to the first target is planned using a Dubins traveling salesperson problem with neighborhoods (DTSPN). The neighborhoods are 3D volumes that satisfy the sensing constraints and are approximated by triangular meshes created using OpenGL. The vertices of the generalized traveling salesperson problem (TSP) are samples from the 3D visibility volumes while the edges of the generalized TSP are Dubins airplane curves.
![Solutions](/3dSolution.png)

## Dependencies
 - Ubuntu 20.04.5 LTS
 - miniconda
 - Docker

## Build Instructions
 - Run ```./deploy/install_dep.sh```
 - Run ```./build.sh```
 - Install python environment ```conda env create -n viewplanning --file environment.yaml```

## Usage Instructions
 - Start database ```docker-compose up -d```
 - Activate python environment ```conda activate viewplanning```
 - Usage with ```python -m viewplanning --help```
 - Test code ```python -m viewplanning test```

## References
1. C. Hague, A. Wolek, A. Willis, and D. Maity, “Planning visual inspection tours for a 3D Dubins airplane model in an urban environment,” in AIAA SciTech Forum 2023. AIAA, January 2023.
## Contact
Collin Hague, chague@uncc.edu