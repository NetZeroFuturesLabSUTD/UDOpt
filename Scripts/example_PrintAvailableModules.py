import sys
sys.path.append('C:\\Users\\jingz\\OneDrive - Singapore University of Technology and Design\\PhD\\202504_UDOpt')
from Utilities.Utilities import *


for generate_task_name in ['ChangeStudyArea','SiteSubdivision','LandUseDensityAllocation','BuildingGeneration']:

    modules_dict = ModulesDict(f'Tasks\\Generate\\{generate_task_name}')

    for module_name, module in modules_dict.items():

        print(generate_task_name, module_name, module.main._bounds)