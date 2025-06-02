import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json, random, copy, datetime
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Real, Integer, Choice, Binary
from pymoo.core.mixed import MixedVariableGA
from pymoo.optimize import minimize

from Utilities.Visualize import *
from Utilities.Utilities import *

# define GA problem
class MixedVariableProblem(ElementwiseProblem):
    def __init__(self, **kwargs):
        self.oUDS = kwargs['oUDS']
        self.Target_GFA = kwargs['Target_GFA']
        self.GA_modules = kwargs['GA_modules']
        self.UDSs = []
        self.filename = kwargs['filename']

        vars = kwargs['GA_vars']
        super().__init__(vars=vars, n_obj=1, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):

        try: # MAIN TRY EXCEPT

            # Sort parameters from gene
            CSA_gene_params = {key.split('_')[1]: X[key] for key in X if 'CSA' in key}
            SS_gene_params = {key.split('_')[1]: X[key] for key in X if 'SS' in key}
            LUDA_fixed_params = {'Target_GFA':self.Target_GFA, 'landuse':'residential'}
            BG_gene_params = {key.split('_')[1]: X[key] for key in X if 'BG' in key}
            
            # Generate tasks
            UDS = copy.deepcopy(self.oUDS)
            UDS = self.GA_modules['CSA'].main(UDS, **CSA_gene_params)
            UDS = self.GA_modules['SS'].main(UDS, **SS_gene_params)
            UDS = self.GA_modules['LUDA'].main(UDS, **LUDA_fixed_params)
            UDS = self.GA_modules['BG'].main(UDS, **BG_gene_params)

            # Evaluation algorithms
            PB_GPRD = ModulesDict('Tasks\\Evaluate\\ParcelBoundaries')['GPRDeviation']
            BF_VO = ModulesDict('Tasks\\Evaluate\\BuildingFootprints')['ViewObstruction']
            BF_AAEUI = ModulesDict('Tasks\\Evaluate\\BuildingFootprints')['ApproxAnnualEUI']
            RC_DR = ModulesDict('Tasks\\Evaluate\\RoadCenterlines')['DensityReach']

            # Evaluate tasks
            UDS = PB_GPRD.main(UDS)
            UDS = BF_VO.main(UDS, distance=100)
            UDS = BF_AAEUI.main(UDS)
            UDS = RC_DR.main(UDS)
            
            # Scalrize 
            metric_bounds = {
                'TotalApproxAnnualEUI': (3012.687698,10390.119831),
                'TotalDensityReach': (638.533991, 2978.264617),
                'TotalGPRDeviation': (0.516661, 51.713601),
                'TotalViewObstruction': (3048.000000, 33445.000000)
            }
            scalarized_score = sum([(value - metric_bounds[key][0]) / (metric_bounds[key][1] - metric_bounds[key][0]) for key, value in UDS['Genotype'].items()])
            UDS['Genotype']['ScalarizedScore'] = scalarized_score

            # Save solutions
            self.UDSs.append(UDS)
            print(len(self.UDSs))
            with open(self.filename, "w") as f:
                f.write(pretty_format_json(self.UDSs, indent=4, max_depth=4))

            out["F"] = scalarized_score
        except:
            out["F"] = 999

GA_modules_combinations = [
    {
        'CSA': ModulesDict('Tasks\\Generate\\ChangeStudyArea')['RandomSelect'],
        'SS': ModulesDict('Tasks\\Generate\\SiteSubdivision')['SimpleVoronoi'],
        'LUDA': ModulesDict('Tasks\\Generate\\LandUseDensityAllocation')['StandardDensify'],
        'BG': ModulesDict('Tasks\\Generate\\BuildingGeneration')['RingOffset']
    }
]

for GA_modules in GA_modules_combinations:

    # Core variables
    nEval = 8
    pop_size = 4
    curr_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"Solutions\\search_MixedVarGA {curr_time}.json"

    # Create mixed variable boundaries for GA problem
    GA_vars = {}
    for task_name, module in GA_modules.items():
        for param_name, param_bounds in module.main._bounds.items():
            if type(param_bounds) == tuple:
                GA_vars[f"{task_name}_{param_name}"] = Real(bounds = param_bounds)
            if type(param_bounds) == list:
                GA_vars[f"{task_name}_{param_name}"] = Choice(options = param_bounds)

    # Load data
    UDSs = json.load(open("Data\\UDS_basic.json"))
    UDS = UDSs[0]
    Target_GFA = np.nansum(GetGFA(UDS)) * 1.3

    # Solve optimisation
    problem = MixedVariableProblem(GA_vars=GA_vars, GA_modules=GA_modules, Target_GFA=Target_GFA, oUDS = UDS, filename=filename)
    algorithm = MixedVariableGA(pop_size=pop_size)
    res = minimize(problem,
                algorithm,
                termination=('n_evals', nEval),
                seed=54321,
                verbose=False)