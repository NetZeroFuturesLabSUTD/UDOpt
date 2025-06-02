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

# Core parameters
nEval = 5
configurations = [
    {'depth':1,'NBranch':32,'IDChainLength':1+(0*4)},
    {'depth':2,'NBranch':16,'IDChainLength':1+(1*4)},
    {'depth':3,'NBranch':8,'IDChainLength':1+(2*4)},
    {'depth':4,'NBranch':4,'IDChainLength':1+(3*4)},
    {'depth':5,'NBranch':2,'IDChainLength':1+(4*4)},
]


# Load data
UDSs = json.load(open("Data\\UDS_basic.json"))
UDS = UDSs[0]
Target_GFA = np.nansum(GetGFA(UDS)) * 1.3
curr_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"Solutions\\search_BreadthFirst {curr_time}.json"

# Search
UDSs = [UDS]
configuration_count = 0
while True:
    depth = configurations[configuration_count]['depth']
    NBranch = configurations[configuration_count]['NBranch']
    IDChainLength = configurations[configuration_count]['IDChainLength']
 
    # Fetch UDS at current depth
    UDS_at_depth = copy.deepcopy([UDS for UDS in UDSs if len(UDS['Metadata']['ID'].split('-')) == IDChainLength])
    
    # For each item on branch
    for UDS_to_iterate in UDS_at_depth:
        
        # Generate a new branch
        for b in range(NBranch):
            try: # MAIN TRY EXCEPT

                UDSs.append(Sample(UDS_to_iterate, Target_GFA))
                print(len(UDSs))

                if len(UDSs)%20==0 or len(UDSs)==nEval:
                    with open(filename, "w") as f:
                        f.write(pretty_format_json(UDSs, indent=4, max_depth=4))
            except:
                pass
            
            if len(UDSs) >= nEval: break
        if len(UDSs) >= nEval: break
    if len(UDSs) >= nEval: break
    configuration_count += 1