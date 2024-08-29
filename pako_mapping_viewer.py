# a small script to visualize the .pako OTF maps for the IRAM 30m telescopes, in order to quickly check the OTF mapping patterns, and find errors in the offsets.
#by Simon Dannhauer, 2024 (dannhauer@ph1.uni-koeln.de/dannhauer@mpifr-bonn.mpg.de)

#USAGE: python pako_mapping_viewer.py --file_name_structure ****hv.pako --num_maps 10 --pako_scripts_directory /path/to/pako_scripts/
#Example: python pako_mapping_viewer.py --file_name_structure notf --num_maps 10 --pako_scripts_directory observing-scripts


import matplotlib.pyplot as plt
import numpy as np
import re
import os
import argparse

def parse_otf_coordinates(file_content):
    pattern = r'OTFMAP\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)'
    return [tuple(map(float, match)) for match in re.findall(pattern, file_content)]

def extract_parameters(file_content):
    notf_matches = re.findall(r'/NOTF\s+(\d+)', file_content)
    step_matches = re.findall(r'/STEP\s+([-\d.]+)\s+([-\d.]+)', file_content)
    
    parameters = []
    for notf, step in zip(notf_matches, step_matches):
        parameters.append((int(notf), float(step[0]), float(step[1])))
    return parameters

def generate_continuous_zigzag(start_x, start_y, end_x, end_y, num_lines, step):
    coordinates = []
    current_y = start_y
    for i in range(num_lines):
        if i % 2 == 0:
            coordinates.append((start_x, current_y))
            coordinates.append((end_x, current_y))
        else:
            coordinates.append((end_x, current_y))
            coordinates.append((start_x, current_y))
        
        if i < num_lines - 1:
            current_y += step
            coordinates.append((end_x if i % 2 == 0 else start_x, current_y))
            coordinates.append((start_x if i % 2 == 0 else end_x, current_y))
    
    return coordinates

def plot_otf_maps(all_coordinates):
    fig, ax = plt.subplots(figsize=(12, 12))
    
    colors = plt.cm.rainbow(np.linspace(0, 1, len(all_coordinates)))
    
    for i, (coordinates, filename) in enumerate(all_coordinates):
        for j, coord_set in enumerate(coordinates):
            x, y = zip(*coord_set)
            label = f"{filename} - OTF {j+1}" if j == 0 else f"_nolegend_"
            ax.plot(x, y, color=colors[i], marker='o', markersize=2, linewidth=1, label=label)
        
    ax.set_xlabel('X Offset (arcsec)')
    ax.set_ylabel('Y Offset (arcsec)')
    ax.set_title('All OTF Mapping Patterns')
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

def visualize_otf_map(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    coordinates_list = parse_otf_coordinates(content)
    parameters_list = extract_parameters(content)
    
    if coordinates_list and parameters_list:
        all_zigzags = []
        for (start_x, start_y, end_x, end_y), (num_lines, step_x, step_y) in zip(coordinates_list, parameters_list):
            if abs(end_x - start_x) > abs(end_y - start_y):  # Horizontal scan
                step = step_y
                zigzag = generate_continuous_zigzag(start_x, start_y, end_x, end_y, num_lines, step)
            else:  # Vertical scan
                step = step_x
                zigzag = generate_continuous_zigzag(start_y, start_x, end_y, end_x, num_lines, step)
                zigzag = [(y, x) for x, y in zigzag]  # Swap x and y for vertical scans
            all_zigzags.append(zigzag)
        
        return all_zigzags, os.path.basename(file_path)
    else:
        print(f"No OTF coordinates found in {file_path}")
        return None

def process_all_files(directory, file_name_structure, num_maps):
    all_coordinates = []
    for i in range(1, num_maps + 1):
        for direction in ['h', 'v']:
            filename = f'{file_name_structure}{i}{direction}.pako'
            file_path = os.path.join(directory, filename)
            if os.path.exists(file_path):
                print(f"Processing {filename}")
                result = visualize_otf_map(file_path)
                if result:
                    all_coordinates.append(result)
            else:
                print(f"File not found: {filename}")
    
    if all_coordinates:
        plot_otf_maps(all_coordinates)
    else:
        print("No valid files found to plot.")

def main():
    parser = argparse.ArgumentParser(description="Plot OTF Mapping Patterns.")
    parser.add_argument('--file_name_structure', type=str, required=True, help="Base name for the OTF files (e.g., 'notf', 'otf').")
    parser.add_argument('--num_maps', type=int, required=True, help="Number of OTF maps (e.g., 10).")
    parser.add_argument('--pako_scripts_directory', type=str, required=True, help="Directory containing the OTF scripts.")
    
    args = parser.parse_args()
    
    process_all_files(args.pako_scripts_directory, args.file_name_structure, args.num_maps)

if __name__ == "__main__":
    main()
