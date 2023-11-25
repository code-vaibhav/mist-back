import os
import re
import pandas as pd
from pymatgen.io.cif import CifParser
import periodictable as pt
def parse_cif_file(file_path):
    atom_site_data = []
    with open(file_path, 'r') as file:
        found_atom_type_partial_charge = False
        index = 0  # Initialize the index
        for line in file:
            if line.strip() == "_atom_type_partial_charge":
                found_atom_type_partial_charge = True
                continue
            if found_atom_type_partial_charge:
                line = line.strip()
                if not line or line.startswith('_'):
                    break
                elements = line.split()
                if len(elements) >= 6:
                    atom_data = {
                        "index": index,  # Add the index to the atom data
                        "atom_name": elements[0],
                        "x": elements[2],
                        "y": elements[3],
                        "z": elements[4],
                        "charge": elements[5]
                    }
                    atom_site_data.append(atom_data)
                    index += 1  # Increment the index
    return atom_site_data
def parse_cif_file_super_box(file_path):
    box_dimensions = {}
    with open(file_path, 'r') as file:
        found_box_dimensions = False
        for line in file:
            if line.strip().startswith("_cell_length_a"):
                elements = line.split()
                if len(elements) >= 2:
                    box_dimensions['a'] = float(elements[1])
                found_box_dimensions = True
            elif line.strip().startswith("_cell_length_b"):
                elements = line.split()
                if len(elements) >= 2:
                    box_dimensions['b'] = float(elements[1])
            elif line.strip().startswith("_cell_length_c"):
                elements = line.split()
                if len(elements) >= 2:
                    box_dimensions['c'] = float(elements[1])

            elif line.strip().startswith("_cell_angle_alpha"):
                elements = line.split()
                if len(elements) >= 2:
                    box_dimensions['alpha'] = float(elements[1])

            elif line.strip().startswith("_cell_angle_beta"):
                elements = line.split()
                if len(elements) >= 2:
                    box_dimensions['beta'] = float(elements[1])

            elif line.strip().startswith("_cell_angle_gamma"):
                elements = line.split()
                if len(elements) >= 2:
                    box_dimensions['gamma'] = float(elements[1])
                    break
                  # Exit loop after getting all dimensions
    return box_dimensions



def parse_cif_file_super_atom(file_path):
    atom_site_data = []

    with open(file_path, 'r') as file:
        found_atom_type_partial_charge = False

        for line in file:
            if line.strip() == "_atom_site_charge":
                found_atom_type_partial_charge = True
                continue

            if found_atom_type_partial_charge:
                line = line.strip()
                if not line or line.startswith('_'):
                    found_atom_type_partial_charge = False
                    continue
                elements = line.split()
                if len(elements) >= 4:
                    atom_data = {
                        "atom_name": elements[0],
                        "x": elements[1],
                        "y": elements[2],
                        "z": elements[3],
                        #"charge": 0
                    }
                    atom_site_data.append(atom_data)

    #print(atom_site_data)
    return atom_site_data




def extract_alphabetic(string):
    return re.sub(r'[^a-zA-Z]', '', string)

folder_path = r'C:\Users\maqib\OneDrive\Documents\JRF_IITK\test_MOF_set\test'
supercell_folder = r'C:\Users\maqib\OneDrive\Documents\JRF_IITK\test_MOF_set\test\supercell_cif'
simulation_folder = folder_path
#os.makedirs(simulation_folder, exist_ok=True)
# UFF potentials
atom_potentials = {
    'Ac': (0.03298759069940, 3.1),
    'Ag': (0.03598826913049, 2.8),
    'Al': (0.50492873016931, 4.01),
    'Am': (0.01398991798336, 3.01),
    'Ar': (0.18496897242772, 3.45),
    'As': (0.30895064614673, 3.77),
    'At': (0.28395161656851, 4.23),
    'Au': (0.03898894756158, 2.93),
    'B': (0.17998108973763, 3.64),
    'Ba': (0.36395646003585, 3.3),
    'Be': (0.08499272615743, 2.45),
    'Bi': (0.51792504602317, 3.89),
    'Bk': (0.01299631585386, 2.97),
    'Br': (0.25096402586911, 3.73),
    'C': (0.10498400100297, 3.43),
    'Ca': (0.23796771001525, 3.03),
    'Cd': (0.22797207259248, 2.54),
    'Ce': (0.01299631585386, 3.17),
    'Cf': (0.01299631585386, 2.95),
    'Cl': (0.22695859842039, 3.52),
    'Cm': (0.01299631585386, 2.96),
    'Co': (0.01398991798336, 2.56),
    'Cr': (0.01500339215545, 2.69),
    'Cu': (0.00500775473268, 3.11),
    'Cs': (0.04499030442376, 4.02),
    'Dy': (0.00699495899168, 3.05),
    'Eu': (0.00800843316377, 3.11),
    'Er': (0.00699495899168, 3.02),
    'Es': (0.01200271372436, 2.94),
    'F': (0.04999805915644, 3),
    'Fe': (0.01299631585386, 2.59),
    'Fm': (0.01200271372436, 2.93),
    'Fr': (0.04999805915644, 4.37),
    'Ga': (0.41494812132179, 3.9),
    'Ge': (0.37893998014871, 3.81),
    'Gd': (0.00900203529327, 3),
    'H': (0.04399670229426, 2.57),
    'Hf': (0.07199641030357, 2.8),
    'Hg': (0.38494133701089, 2.41),
    'Ho': (0.00699495899168, 3.04),
    'I': (0.33895743045763, 4.01),
    'In': (0.59892349162001, 3.98),
    'Ir': (0.07299001243307, 2.53),
    'K': (0.03499466700099, 3.4),
    'Kr': (0.21996363942871, 3.69),
    'La': (0.01699059641445, 3.14),
    'Li': (0.02499902957822, 2.18),
    'Lu': (0.04099602386317, 3.24),
    'Lr': (0.01098923955227, 2.88),
    'Md': (0.01098923955227, 2.92),
    'Mg': (0.11098535786515, 2.69),
    'Mn': (0.01299631585386, 2.64),
    'Mo': (0.05599941601862, 2.72),
    'N': (0.06899573187248, 3.26),
    'Na': (0.02998691226831, 2.66),
    'Ne': (0.04198962599267, 2.66),
    'Nb': (0.05900009444971, 2.82),
    'Nd': (0.00999563742277, 3.18),
    'No': (0.01098923955227, 2.89),
    'Ni': (0.01500339215545, 2.52),
    'Np': (0.01899767271604, 3.05),
    'O': (0.05999369657921, 3.12),
    'Os': (0.03700174330258, 2.78),
    'P': (0.30495636558614, 3.69),
    'Pa': (0.02199835114713, 3.05),
    'Pb': (0.66291146875981, 3.83),
    'Pd': (0.04799098285485, 2.58),
    'Pm': (0.00900203529327, 3.16),
    'Pu': (0.01599699428495, 3.05),
    'Ra': (0.40393900972693, 3.28),
    'Rb': (0.04000242173367, 3.67),
    'Re': (0.06599505344139, 2.63),
    'Rh': (0.05299873758753, 2.61),
    'Rn': (0.24796334743802, 4.25),
    'Ru': (0.05599941601862, 2.64),
    'S': (0.27395597914574, 3.59),
    'Sb': (0.44892931415069, 3.94),
    'Sc': (0.01899767271604, 2.94),
    'Se': (0.29096644760278, 3.75),
    'Si': (0.40195180546793, 3.83),
    'Sm': (0.00800843316377, 3.14),
    'Sn': (0.56690963100752, 3.91),
    'Sr': (0.23496703158416, 3.24),
    'Ta': (0.08097857355425, 2.82),
    'Tb': (0.00699495899168, 3.07),
    'Tc': (0.04799098285485, 2.67),
    'Te': (0.39793765286475, 3.98),
    'Th': (0.02599263170772, 3.03),
    'Ti': (0.01699059641445, 2.83),
    'TI': (0.67990206517426, 3.87),
    'Tm': (0.00600135686218, 3.01),
    'U': (0.02199835114713, 3.02),
    'V': (0.01599699428495, 2.8),
    'W': (0.06698865557089, 2.73),
    'Xe': (0.33194259942336, 3.92),
    'Y': (0.07199641030357, 2.98),
    'Yb': (0.22797207259248, 2.99),
    'Zn': (0.12398167371901, 2.46),
    'Zr': (0.06899573187248, 2.78),
    'Po': (0.32494764043168, 4.2),
    'Pr': (0.00999563742277, 3.21),
    'Pt': (0.07998497142475, 2.45),
}

atomic_masses = {
    'H': 1.00784,
    'C': 12.0116,
    'N': 14.00728,
    'O': 15.99977,
    'F': 18.99840316,
    'P': 30.973762,
    'S': 32.076,
    'Cl': 35.457,
    'V': 50.9415,
    'Cr': 51.9961,
    'Ni': 58.6934,
    'Cu': 63.546,
    'Zn': 65.38,
    'Br': 79.907,
    'I': 126.90447,
    'Ba': 137.327,
    'Zr':91.224
}

# New directory for .pot files
#pot_files_dir = os.path.join(folder_path, 'cif_pot_files')
#os.makedirs(pot_files_dir, exist_ok=True)

cif_files = [file for file in os.listdir(folder_path) if file.endswith('.cif')]
super_cif_file = [file for file in os.listdir(supercell_folder) if file.endswith('.cif')]
#simulation_folder = r'/home/user/Project_JRF/Tobascco_MOF/Simulation'
#os.makedirs(simulation_folder, exist_ok=True)
count = 1
# Loop
for cif_file in cif_files:
    # Pot file
    pot_file_path = os.path.join(simulation_folder, os.path.splitext(cif_file)[0] + '.pot')

    # CifParser
    cif_file_path = os.path.join(folder_path, cif_file)
   # parser = CifParser(cif_file_path)
   # structure = parser.get_structures()[0]
    parsed_data = parse_cif_file(cif_file_path)

    # Unique atom set and charge dictionary
   # unique_atoms = set()

    # Extracting unique atom symbols from the structure
   # for site in structure.sites:
   #     symbol = site.specie.symbol
   #     unique_atoms.add(symbol)
    atom_count = 0
    for atom in parsed_data:
        atom_count += 1
    #print(atom_count)
    # Writing data to the .pot file
    with open(pot_file_path, 'w') as pot_file:
        pot_file.write("# CIF - {}\n\n".format(cif_file))

        pot_file.write("NATOM {}\n".format(atom_count))
        pot_file.write("N_ATOM_TYPE {}\n\n".format(atom_count))

        pot_file.write("POTENTIAL_COEFF lj_coul 12.8 # (aid, name, eps, sig, mass, charge)\n")
        aid = 1
        for atom in parsed_data:
            symbol = extract_alphabetic(atom['atom_name'])
            eps, sig = atom_potentials.get(symbol, (0.0, 0.0))
            charge = atom['charge']
            mass = pt.elements.symbol(symbol).mass
            pot_file.write("{} {} {} {} {} {}\n".format(aid, symbol, eps, sig, mass, charge))
            aid += 1

    #new_folder_path = os.path.join(folder_path, 'mist_data_files')
    mistdata_file_path = os.path.join(simulation_folder, os.path.splitext(cif_file)[0] + '.mistdata')
    for super_cif_files in super_cif_file:
        if super_cif_files == cif_file:
            break



    cif_supercell_file = os.path.join(supercell_folder, super_cif_files)

    supercell_data = parse_cif_file_super_atom(cif_supercell_file)

    box_dimension = parse_cif_file_super_box(cif_supercell_file)
    atom_count_s = 0
    for atom in supercell_data:
        atom_count_s += 1

    with open(mistdata_file_path, 'w') as mistdata_file:
        mistdata_file.write("# CIF - {}\n\n".format(cif_file))

        mistdata_file.write("dimension\n")
        mistdata_file.write("{} {}\n".format(box_dimension.get('a'),box_dimension.get('alpha')))
        mistdata_file.write("{} {}\n".format(box_dimension.get('b'),box_dimension.get('beta')))
        mistdata_file.write("{} {}\n\n".format(box_dimension.get('c'),box_dimension.get('gamma')))

        mistdata_file.write("molecule_types 5\n\n")

        mistdata_file.write("molecule # (mol_typ, atom_type, nsite, nmol, status)\n")
        mistdata_file.write("1 3 12 0 fluid\n")
        mistdata_file.write("2 3 12 0 fluid\n")
        mistdata_file.write("3 3 12 0 fluid\n")
        mistdata_file.write("4 6 18 0 fluid\n")
        mistdata_file.write("5 {} 1 {} rigid\n\n".format(atom_count, atom_count_s))

        mistdata_file.write("coords # (i, mol_id, atyp, x, y, z)\n")
        j=1

        for atom in supercell_data:
         for index, parsed_atom in enumerate(parsed_data):
            if parsed_atom["atom_name"] == atom["atom_name"]:
              num=index+16


              mistdata_file.write("{} 1 {} {} {} {}\n".format(j, num, round(float(atom['x']),9), round(float(atom['y']), 9), round(float(atom['z']),9)))
              break
         j += 1

    print("Done {} {}".format(cif_file, count))
    count += 1
