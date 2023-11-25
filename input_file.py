import os
from pymatgen.io.cif import CifParser

folder_path = r'C:\Users\maqib\OneDrive\Documents\JRF_IITK\test_MOF_set\test'

new_folder_path = os.path.join(folder_path, 'input_files')
#os.makedirs(new_folder_path, exist_ok=True)

# Loop through each .cif file
cif_files = [file for file in os.listdir(folder_path) if file.endswith('.cif')]
for cif_file in cif_files:
    cif_file_path = os.path.join(folder_path, cif_file)

    
    input_file_path = os.path.join(folder_path,os.path.splitext(cif_file)[0] + '.file')
    
    with open(input_file_path, 'w') as input_file:
        input_file.write("# CIF - {}\n\n".format(cif_file))
        input_file.write("unit real\n\n")
        input_file.write("ensemble GCMC\n\n")
        input_file.write("dimension 3\n\n")
        input_file.write("box 1 triclinic\n\n")
        input_file.write("datafile\n")
        input_file.write("1 fractional {}".format((os.path.splitext(cif_file)[0]) + '.mistdata'))
        input_file.write("\n\npotfile\n")
        input_file.write("1 pX.pot\n")
        input_file.write("2 mX.pot\n")
        input_file.write("3 oX.pot\n")
        input_file.write("4 eb.pot\n")
        input_file.write("5 {}".format(os.path.splitext(cif_file)[0]) + '.pot')
        input_file.write("\n\ncondition 373 -10.02038660 -9.50660706 -10.02038660 -10.84215748\n\n")
        input_file.write("move 4\n")
        input_file.write("add_remove 0.6\n")
        input_file.write("displace 0.15\n")
        input_file.write("rotate 0.15\n")
        input_file.write("swap 0.1\n\n")
        input_file.write("equil_run    2000\n")
        input_file.write("prod_run    5000\n")
        input_file.write("sweep 1000\n\n")
        input_file.write("write_data xyz 1000 dump.xyz\n")
        input_file.write("write_prop 100\n")
        input_file.write("prop 10 nmolecule")