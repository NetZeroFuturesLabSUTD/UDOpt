import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json, random, copy, datetime
import numpy as np

from Utilities.Visualize import *
from Utilities.Utilities import *

def GetRandomParams(module):
    params = {}
    for key,value in module.main._bounds.items():
        if type(value) == tuple:
            params[key] = random.uniform(float(value[0]), float(value[1]))
        if type(value) == list:
            params[key] = random.choice(value)
    return params

def Sample(oUDS, Target_GFA):
    UDS = copy.deepcopy(oUDS)
    
    # Load partially random generative algorithms
    CSA_random_module = random.choice(list(ModulesDict('Tasks\\Generate\\ChangeStudyArea').values()))
    SS_random_module = random.choice(list(ModulesDict('Tasks\\Generate\\SiteSubdivision').values()))
    LUDA_StandardDensify = ModulesDict('Tasks\\Generate\\LandUseDensityAllocation')['StandardDensify']
    BG_random_module = random.choice(list(ModulesDict('Tasks\\Generate\\BuildingGeneration').values()))

    # Randomize parameters to use
    CSA_random_params = GetRandomParams(CSA_random_module)
    SS_random_params = GetRandomParams(SS_random_module)
    LUDA_fixed_params = {'Target_GFA':Target_GFA, 'landuse':'residential'}
    BG_random_params = GetRandomParams(BG_random_module)

    # Evaluation algorithms
    PB_GPRD = ModulesDict('Tasks\\Evaluate\\ParcelBoundaries')['GPRDeviation']
    BF_VO = ModulesDict('Tasks\\Evaluate\\BuildingFootprints')['ViewObstruction']
    BF_AAEUI = ModulesDict('Tasks\\Evaluate\\BuildingFootprints')['ApproxAnnualEUI']
    RC_DR = ModulesDict('Tasks\\Evaluate\\RoadCenterlines')['DensityReach']


    # Generate tasks
    UDS = CSA_random_module.main(UDS, **CSA_random_params)
    UDS = SS_random_module.main(UDS, **SS_random_params)
    UDS = LUDA_StandardDensify.main(UDS, **LUDA_fixed_params)
    UDS = BG_random_module.main(UDS, **BG_random_params)

    # Evaluate tasks
    UDS = PB_GPRD.main(UDS)
    UDS = BF_VO.main(UDS, distance=100)
    UDS = BF_AAEUI.main(UDS)
    UDS = RC_DR.main(UDS)
    return UDS

# load data
UDSs = json.load(open("Data\\UDS_basic.json"))
UDS = UDSs[0]
Target_GFA = np.nansum(GetGFA(UDS)) * 1.3

nEval = 5
curr_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"Solutions\\search_RandomSample {curr_time}.json"

while len(UDSs) <= nEval:

    try: # MAIN TRY EXCEPT
        UDSs.append(Sample(UDS, Target_GFA))

        # Save solution
        print(len(UDSs))
        
        if len(UDSs)%20==0 or len(UDSs)==nEval:
            with open(filename, "w") as f:
                f.write(pretty_format_json(UDSs, indent=4, max_depth=4))
    
    except Exception as e:
        print(e)