""" 
Common parameters for the modelling

"""
import os
from os.path import join

from pyparsing import Enum


def get_project_root():
    """Return the path to the project root directory.
    :return: A directory path.
    :rtype: str
    """
    return os.path.realpath(os.path.join(
        os.path.dirname(__file__),
        os.pardir,
    ))


BASE_DIR = get_project_root()
DATA_DIR = join(BASE_DIR, "data")
MODEL_DIR = join(BASE_DIR, "model")
RESULTS_DIR = join(BASE_DIR, "results")
RESULTS_DATA_DIR = join(RESULTS_DIR, "data")
RESULTS_VIS_DIR = join(RESULTS_DIR, "visualizations")


class Districts(Enum):
    '''
    Each scenario represents a district
    '''
    ENAQ = {"val":1, "name":"ENaQ"}				
    QUARREE100 = {"val":2, "name":"Quarree100"}
    SQ50 = {"val":3, "name": "Stadtquartier50"} # Stadtquartier50
    ZED = {"val":4, "name":	"ZED"}
    NWS = {"val":5, "name": "Neue Weststadt"}# Neue Weststadt
    #PFAFF = {"val":1, "name":"PFAFF"}


if __name__ == '__main__':
    print(BASE_DIR)

    distr = Districts.ENAQ
    print(distr.name)
    print(distr.value["name"])
    

    pass



