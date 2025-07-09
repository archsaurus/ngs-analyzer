from src.core.base import *
from src.core.dependency_handler import DependencyHandler

class ConfigurationError(Exception): pass

class Configurator(metaclass=SingletonMeta):

    def __init__(
        self,
        log_path: PathLike[AnyStr]=os.path.abspath(os.path.join(os.path.curdir, 'logs'))
    ):
        self.args = self.parse_argvars()
        self.log_path = log_path

        # Set logging
        self.logger = self.set_logger(silent=False)
        try: os.mkdir(log_path)
        except FileExistsError: self.logger.info(f"Logger base path set to '{log_path}'")

        self.output_dir = self.set_output_directory(self.args.outputDir)
        self.config = self.parse_configuration()

    def parse_argvars(self) -> argparse.Namespace:
        """Set a list of command line arguments and return a compiled object stored these arguments attributes."""
        parser = argparse.ArgumentParser(description='This script do all processing of BRCA sequencing data')
        arguments = [
            {'name': ('--log-file',                 '-l'), 'kwargs': {'dest': 'logFilename',     'type':   str,          'help': 'use non-default logger. Default logger named "./brca_analyzer.log"',                                                                                                                                                                                           'default':  'brca_analyzer.log'}},
            {'name': ('--output-dir',               '-o'), 'kwargs': {'dest': 'outputDir',       'type':   str,          'help': 'directory for output',                                                                                                                                                                                                                                        'required':                 True}},
            {'name': ('--language',                 '-L'), 'kwargs': {'dest': 'lang',            'type':   str,          'help': 'Language of report and text on figures (russian or english). Default is english',                                                                                                                                                                              'default':            'english'}},

            {'name': ('--readsFiles_r1',           '-r1'), 'kwargs': {'dest': 'readsFiles1',     'type':   str,          'help': 'regular expression for choosing files with R1 reads',                                                                                                                                                                                                         'required':                 True}},
            {'name': ('--readsFiles_r2',           '-r2'), 'kwargs': {'dest': 'readsFiles2',     'type':   str,          'help': 'regular expression for choosing files with R2 reads (optional)',                                                                                                                                                                                              'required':                False}},
            {'name': ('--readsFiles_N',            '-rN'), 'kwargs': {'dest': 'readsFilesN',     'type':   str,          'help': 'regular expression for choosing files with native R1 reads (including Undetermined) to evaluate effectivity of trimming reads (alternative). If you do not have trimmed reads, do not use this parameter',                                                   'required':                False}},
            {'name': ('--minimal-read-length', '-minlen'), 'kwargs': {'dest': 'minReadLen',      'type':   int,          'help': 'minimal length of read after trimming. Default: 30',                                                                                                                                                                                                           'default':                   30}},
            {'name': ('--primersFileR1_3',       '-pr13'), 'kwargs': {'dest': 'primersFileR1_3', 'type':   str,          'help': 'fasta-file with sequences of primers on the 3\'-end of R1 reads. Use it, only if you need to cut primer sequences from reads. It is not required. But if it is determined, -pr23 is necessary',                                                               'required':                False}},
            {'name': ('--primersFileR2_3',       '-pr23'), 'kwargs': {'dest': 'primersFileR2_3', 'type':   str,          'help': 'fasta-file with sequences of primers on the 3\'-end of R2 reads. Use it, only if you need to cut primer sequences from reads.',                                                                                                                               'required':                False}},
            {'name': ('--primersFileR1_5',       '-pr15'), 'kwargs': {'dest': 'primersFileR1_5', 'type':   str,          'help': 'fasta-file with sequences of primers on the 5\'-end of R1 reads. Use it, only if you need to cut primer sequences from reads',                                                                                                                                'required':                False}},
            {'name': ('--primersFileR2_5',       '-pr25'), 'kwargs': {'dest': 'primersFileR2_5', 'type':   str,          'help': 'fasta-file with sequences of primers on the 5\'-end of R2 reads. Use it, only if you need to cut primer sequences from reads. Also, do not use this parameter if you have single-end reads',                                                                  'required':                False}},
            {'name': ('--primer-location-buffer', '-plb'), 'kwargs': {'dest': 'primerLocBuf',    'type':   int,          'help': 'buffer of primer location in the read from the start or end of read. If this value is zero, then cutPrimers will search for primer sequence in the region of the longest primer length. Default: 10',                                                          'default':                   10}},
            {'name': ('--primersCoords',       '-primer'), 'kwargs': {'dest': 'primersCoords',   'type':   str,          'help': 'table with information about amplicon coordinates without column headers: amplicon_number | chromosome | start | end. (Is not required)',                                                                                                                     'required':                False}},
            {'name': ('--primer3-absent',     '-primer3'), 'kwargs': {'dest': 'primer3absent',   'action': 'store_true', 'help': "if primer at the 3'-end may be absent, use this parameter"                                                                                                                                                                                                                                    }},
            {'name': ('--coordinates-file',     '-coord'), 'kwargs': {'dest': 'coordsFile',      'type':   str,          'help': 'file with coordinates of amplicons in the BED-format (without column names and locations of primers): chromosome | start | end. It is necessary for cutting primer sequences from BAM-file. Its order should be the same as for files with primer sequences', 'required':                False}},
            {'name': ('--patientsTable',          '-pat'), 'kwargs': {'dest': 'patientsTable',   'type':   str,          'help': 'table with information about each patient: ngs_num patient_id barcode1 barcode2',                                                                                                                                                                             'required':                False}},
            {'name': ('--error-number',           '-err'), 'kwargs': {'dest': 'errNumber',       'type':   int,          'help': 'number of errors (substitutions, insertions, deletions) that allowed during searching primer sequence in a read sequence. Default: 3',                                                                                                                         'default':                    3}},
            {'name': ('--run-name',               '-run'), 'kwargs': {'dest': 'runName',         'type':   str,          'help': 'this name will be added into the name of the final output file. Default: BRCA',                                                                                                                                                                   'default':               'BRCA'}},
            {'name': ('--without-joinment',   '-notjoin'), 'kwargs': {'dest': 'notToJoin',       'action': 'store_true', 'help': 'use this parameter if you only want to process patients reads separately without joining them (useful if you have an opportunity to separate processing onto several machines)'                                                                                                               }},
            {'name': ('--only-join',         '-onlyjoin'), 'kwargs': {'dest': 'onlyJoin',        'action': 'store_true', 'help': 'use this parameter if you only want to join already processed patients reads'                                                                                                                                                                                                                 }},
            {'name': ('--tool-threads',            '-tt'), 'kwargs': {'dest': 'toolThreads',     'type':   int,          'help': 'number of threads for each tool. Number of --threads multiplied by the number of --tool-threads must not exceed number of CPU cores',                                                                                                                          'default':                    1}},
            {'name': ('--threads',                 '-th'), 'kwargs': {'dest': 'threads',         'type':   int,          'help': 'number of threads',                                                                                                                                                                                                                                            'default':                    2}},
        ]
        
        for arg in arguments:
            # TODO: Validate input arguments
            parser.add_argument(*arg['name'], **arg['kwargs'])
        return parser.parse_args()

    def set_logger(self, silent: bool=False):
        try:
            base_logpath = os.path.abspath(os.path.join(self.log_path, self.args.logFilename))
            if not DependencyHandler.verify_path(base_logpath): exit(os.EX_SOFTWARE)

            handlers=[logging.FileHandler(filename=base_logpath)]
            if not silent: handlers.append(logging.StreamHandler(stream=sys.stdout))
            logging.basicConfig(level=logging.INFO, format=r'%(asctime)s - %(levelname)s - %(message)s', handlers=handlers)
            
            configuration_logger = logging.getLogger()
            configuration_logger.propagate = False
            return configuration_logger
        except Exception as e:
            print(f"A fatal error '{e.__repr__()}' occured at '{e.__traceback__.tb_frame}'", file=sys.stdout)
            exit(os.EX_SOFTWARE)

    def set_output_directory(self, output_dir: PathLike[AnyStr]) -> PathLike[AnyStr]:
        """Get the output directory path and validate it for existing as a directory."""
        output_dir = os.path.abspath(os.path.normpath(output_dir))

        if os.path.exists(output_dir): # Create output directory
            if not os.path.isdir(output_dir): os.mkdir(output_dir)
            else:
                msg = f"Directory '{output_dir}' already exists"
                self.logger.warning(msg)
                match input(f"Do you want to use existing directory '{output_dir}' as the current output directory [y/n]: ").lower():
                    case 'n': exit(os.EX_OK)
                    case  _ : pass
        else: os.mkdir(output_dir)

        self.logger.info(f"Use '{output_dir}' directory as output")
        return output_dir

    def parse_configuration(
        self,
        base_config_filepath: PathLike[AnyStr]=os.path.join(os.path.curdir, 'src', 'conf', 'config.ini'),
        target_section: AnyStr='Pathes'
    ) -> dict:
        if os.path.exists(base_config_filepath) and os.path.isfile(base_config_filepath):
            conf = configparser.ConfigParser(inline_comment_prefixes=[';', '#'], comment_prefixes=[';', '#'])
            conf.read(os.path.join(base_config_filepath))

            config_dict = {'target_section': target_section}
            if target_section in conf:
                for path_value in conf[target_section]: config_dict[path_value] = conf[target_section][path_value]
            else: raise ConfigurationError(f"Can't parse configuration file under path '{base_config_filepath}'. See the project config documentattion")
            return config_dict
        else:
            self.logger.critical(msg=f"Can't find configuration file under path '{base_config_filepath}'")
            raise FileNotFoundError()
