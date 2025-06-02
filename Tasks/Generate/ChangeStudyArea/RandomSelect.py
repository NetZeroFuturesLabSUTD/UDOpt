import random
from Utilities.Utilities import *

@enforce_bounds({'k': (1, 5),'seed': (1,2**32)})
def main(UDS,k=4,seed=1):
    random.seed(int(seed))
    SAs = UDS['Phenotype']['StudyAreas']

    k = int(k)
    if k > len(SAs): k = len(SAs)

    random_SAs = random.sample(SAs, k = k)

    boundaries = [shape(SA['geometry']) for SA in random_SAs]
    _, UDS = IncludeUDSWithinBoundaries(UDS, boundaries)

    UDS['Phenotype']['StudyAreas'] = random_SAs

    UDS = UpdateID(UDS)
    UDS = UpdateParameters(UDS,{'RandomSelect':{'k':k, 'seed':int(seed)}})
    
    return UDS



