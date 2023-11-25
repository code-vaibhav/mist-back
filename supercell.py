import os
import re
import numpy as np

def parse_cif_file(file_path):
    atom_site_data = []
    with open(file_path, 'r') as file:
        found_atom_type_partial_charge = False
        index = 1  # Initialize the index
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
                       # "index": index,  # Add the index to the atom data
                        "atom_name": elements[0],
                        "x": elements[2],
                        "y": elements[3],
                        "z": elements[4],
                        
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





import numpy as np

def create_supercell(parsed_data, box_dimensions, supercell_size):
    basis_vectors = np.array([[box_dimensions.get('a'), 0, 0],
                              [0, box_dimensions.get('b'), 0],
                              [0, 0, box_dimensions.get('c')]])  # Basis vectors a, b, c
    
    
    p = np.array([0.0, 0.0, 0.0])  # Shift vector p

    # Supercell dimensions
    nx = supercell_size[0]  # Number of unit cells in x-direction
    ny = supercell_size[1]  # Number of unit cells in y-direction
    nz = supercell_size[2]  # Number of unit cells in z-direction
    P = np.diag([1/nx,1/ny,1/nz])
    
    # Calculate the new basis vectors for the supercell
    a_prime = np.dot(basis_vectors[0], P)
    b_prime = np.dot(basis_vectors[1], P)
    c_prime = np.dot(basis_vectors[2], P)
    
    # Calculate the shift of origin for the supercell
    t = np.dot(basis_vectors, p)
    
    # Load the atom positions from coordinates
    atom_positions = []
    for atom in parsed_data:
        x = float(atom['x'])
        y = float(atom['y'])
        z = float(atom['z'])
        atom_positions.append([x, y, z])
    # Create the supercell atom positions
    supercell_positions = []
    for ix in range(nx):
        
        x_ = ix/nx
        
        for iy in range(ny):
            y_ = iy/ny
            
            for iz in range(nz):
                z_ = iz/nz
                t = np.array([x_,y_,z_])
                
                
                
                shift = np.dot(atom_positions, P.T) + t
                supercell_positions.extend(shift)
    # Create a list of tuples with atom names and fractional coordinates
    supercell_atoms = []
    for i, position in enumerate(supercell_positions):
        atom = parsed_data[i % len(parsed_data)]
        atom_name = atom['atom_name']
        x, y, z = position
        
        
        supercell_atoms.append((atom_name, x, y, z))
    
    return supercell_atoms
   

def parse_cif_file_super_atom(file_path):
    atom_site_data = []
    
    with open(file_path, 'r') as file:
        found_atom_type_partial_charge = False
        
        for line in file:
            if line.strip() == "_atom_site_fract_z":
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
                        "charge": 0
                    }
                    atom_site_data.append(atom_data)
            
          
    return atom_site_data

def write_supercell_cif(supercell_data, box_dimensions, supercell_file_path, supercell_size):
    with open(supercell_file_path, 'w') as file:
        # Write the box dimensions
        file.write("data_str_m1_o10_o10_f0_pcu.sym.100\n_audit_creation_date              2012-12-10T16:35:05-0500\n_audit_creation_method            fapswitch 2.2\n")

        file.write("_symmetry_space_group_name_H-M    P1\n")
        file.write("_symmetry_Int_Tables_number       1\n")
        file.write("_space_group_crystal_system       triclinic\n")
        file.write("_cell_length_a {}\n".format(box_dimensions.get('a', 0)*supercell_size[0]))
        file.write("_cell_length_b {}\n".format(box_dimensions.get('b', 0)*supercell_size[1]))
        file.write("_cell_length_c {}\n".format(box_dimensions.get('c', 0)*supercell_size[2]))
        file.write("_cell_angle_alpha {}\n".format(box_dimensions.get('alpha', 0)))
        file.write("_cell_angle_beta {}\n".format(box_dimensions.get('beta', 0)))
        file.write("_cell_angle_gamma {}\n".format(box_dimensions.get('gamma', 0)))
        
        # Write the atom site data
        file.write("loop_\n")
        file.write("_atom_site_label\n")
        file.write("_atom_site_fract_x\n")
        file.write("_atom_site_fract_y\n")
        file.write("_atom_site_fract_z\n")
        file.write("_atom_site_charge\n")
        
        for atom in supercell_data:
            file.write("{} {} {} {}\n".format(
                atom[0],
                atom[1],
                atom[2],
                atom[3],
            ))



def extract_alphabetic(string):
    return re.sub(r'[^a-zA-Z]', '', string)

folder_path = r'C:\Users\maqib\OneDrive\Documents\JRF_IITK\test_MOF_set\test'
supercell_folder = r'C:\Users\maqib\OneDrive\Documents\JRF_IITK\test_MOF_set\test\supercell_cif'
#simulation_folder = r'/home/user/Project_JRF/Tobascco_MOF/test_MOF_set/prosun_test'
os.makedirs(supercell_folder, exist_ok=True)


cif_files = [file for file in os.listdir(folder_path) if file.endswith('.cif')]
super_cif_file = [file for file in os.listdir(supercell_folder) if file.endswith('.cif')]
count = 1
# Loop
for cif_file in cif_files:
    # Pot file
    supercell_file_path = os.path.join(supercell_folder, os.path.splitext(cif_file)[0] + '_supercell.cif')

    # CifParser
    cif_file_path = os.path.join(folder_path, cif_file)
   
    parsed_data = parse_cif_file(cif_file_path)
    box_dimensions = parse_cif_file_super_box(cif_file_path)
    
    if box_dimensions['a'] < 3.0 or box_dimensions['b'] < 3.0 or box_dimensions['c'] < 3.0:
        continue
    supercell_size=[]
    for i in range(10):
        if box_dimensions.get('a') * i > 26.0:
            supercell_size.append(i)
            break
    for i in range(10):
        if box_dimensions.get('b') * i > 26.0:
            supercell_size.append(i)
            break
    for i in range(10):
        if box_dimensions.get('c') * i > 26.0:
            supercell_size.append(i)
            break
    print(supercell_size)
    rotation_matrix=np.array([[supercell_size[0],0,0],[0,supercell_size[0],0],[0,0,supercell_size[0]]])
    
    supercell_data = create_supercell(parsed_data, box_dimensions, supercell_size)


   # print(supercell_data)
    write_supercell_cif(supercell_data, box_dimensions, supercell_file_path, supercell_size)

    
    atom_count = 0
    for atom in parsed_data:
        atom_count += 1
    #print(atom_count)
    # Writing data to the .pot file
    
  # Example supercell size


    #print("Done {} {}".format(cif_file, count))
    count += 1