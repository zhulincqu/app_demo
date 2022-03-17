import os
import re
import numpy as np

def read_file(path_filename):
    return Reader(path_filename)
    

class Reader():
    __slots__ = (
        "metadata",
        "spectrum",
        "path_filename",
    )

    def __init__(self, path_filename=None):
        if path_filename is None:
            pass
        else: 
            self.path_filename = path_filename
            self.metadata = {}
            self.spectrum = {}
            self._read_txt(path_filename)
            self._spectrum2array()
         
    def _read_txt(self, path_filename):
        """
        Function read data and metadata from one file 
        
        is calculated iteratively and then subtracted from the dataset.
        
        Args:
        path_filename (str): filename and path to the file 
        
        Returns:
        Tuple(data, metadata): spectrum are save in data, while other
        meta data are saved in metadata dict.
        """
        
        if os.path.isfile(path_filename):  
            with open(path_filename, "r") as f:
                f.readline() # skip first line [Info]
                num_regions = int(f.readline().split("=")[1].strip()) # check number of regions
                # print(num_regions)
                version = f.readline().split("=")[1].strip() # check the file version
                # print(version)
                region_head =re.compile(r"^\[Region ([0-9]*)\]$") 
                if version in ["1.3.1"]:
                    metadata_section = []
                    spectrum_section = []
                    current_section = ""
                    # print(full_data)
                    while line := f.readline():
                        line = line.strip()
                        if mo := re.match(region_head, line):
                            region_num = mo.group(1)
                            region_key = f"Region {region_num}"
                            self.metadata[region_key] = {}
                            metadata_section = [f"[Info {region_num}]", f"[Run Mode Information {region_num}]"]
                            spectrum_section = [f"[Data {region_num}]"]
                            # print(region_key)
                            current_section = "metadata"
                            continue
                        elif line in metadata_section: 
                            # print(line)
                            current_section = "metadata"
                            continue
                        elif line in spectrum_section:
                            # print(line)
                            current_section = "spectrum"
                            self.spectrum[region_key] = list()
                            continue
                        elif line == "": # skip the blank line
                            continue

                        if current_section == "metadata": 
                            key, value = line.split("=")
                            self.metadata[region_key][key] = value
                        elif current_section == "spectrum":
                            bing_energy, intensity = line.split("  ") # double space
                            self.spectrum[region_key].append([float(bing_energy), float(intensity)])
                            # print(float(bing_energy), float(intensity))
                            pass
                            # print(line)
                else: 
                    print(f"Can not read file version {version}")
                    return
                # print(full_data["Region 1"]["spectrum"])

        else:
            print("Can not find the file!")
            return 
        
    def _spectrum2array(self):
        for region in self.spectrum.keys():
            self.spectrum[region] = np.array(self.spectrum[region])


if __name__ == "__main__":

    # test codes 
    data = Reader()
    data = read_file(r"..\Archive\plot\XPS_0001.txt")
    data = read_file(r"C:\Users\linzhu\Documents\Jupyter\Archive\fit_gauss\Fit_gauss1.txt")