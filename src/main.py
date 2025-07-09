from src.core.base import *

from src.core.patient_data_container import PatientDataContainer
from src.core.analyzer import Analyzer

from src.settings import dependency_handler, configurator

if __name__ == '__main__':
    brca1_analyzer = Analyzer()
    brca1_analyzer.context.update(
        brca1_analyzer.prepareData(patient=PatientDataContainer(
            id=0,
            R1_source=configurator.args.readsFiles1,
            R2_source=configurator.args.readsFiles2
        ))
    )
    
    brca1_analyzer.analyze()
