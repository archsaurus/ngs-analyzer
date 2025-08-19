# NGS Analyzer

[![Read the Docs](https://readthedocs.org/projects/ngs-analyzer/badge/?version=latest)](https://ngs-analyzer.readthedocs.io/en/latest/)
[![License](https://img.shields.io/github/license/archsaurus/ngs-analyzer)](LICENSE)
![Codecov](https://codecov.io/gh/archsaurus/ngs-analyzer/branch/dev/graph/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)
![pip Version](https://img.shields.io/badge/pip-25.2%2B-green)
![Java Version](https://img.shields.io/badge/java_SE-24%2B-red)

---

## Overview

**NGS Analyzer** is a comprehensive python-based pipeline designed for amplicon-based NGS data analysis. It streamlines processes such as demultiplexing, read alignment, variant calling, and annotation, providing researchers with a powerful tool for genomics research.

## Installation

### Prerequisites

- [Python 3.13+](https://www.python.org/)
- [pip 25.2+](https://pypi.org/project/pip/)
- [Java 8](https://www.java.com/)
- C/C++ compiler ([GCC](https://gcc.gnu.org/), [Clang](https://clang.llvm.org/), [MinGV](https://mingw-w64.org/), etc.)

### Python Requirements

#### On Linux/Mac:

```bash
python -m pip install -r requirements.txt
```

##### On Windows:

```powershell
C:\Path\To\Python\python.exe -m pip install -r requirements.txt
```

Or, if python is in your PATH environment varriable,

```powershell
python.exe -m pip install -r requirements.txt
```

### External Dependencies

The project also relies on several external tools. Please ensure these are installed and their paths in your configuration.

[bcl2fastq2](https://support.illumina.com) | Converts Illumina BCL files to FASTQ files.

[bwa-mem2](https://github.com/bwa-mem2/bwa-mem2) | Fast aligner for sequencing reads.

[Trimmomatic](http://www.usadellab.org/cms/?page=trimmomatic) | Read trimming tool.

[pTrimmer](https://github.com/DMU-lilab/pTrimmer) | Adapter trimming and quality control.

[Picard](https://broadinstitute.github.io/picard/) | Toolkit for manipulating high-throughput sequencing data.

[Genome Analysis Toolkit](https://gatk.broadinstitute.org/hc/en-us) | Genome Analysis Toolkit for variant discovery.

[samtools](http://www.htslib.org/) | Utilities for manipulating alignments and variant calling.

[bedtools](https://github.com/arq5x/bedtools2) | Genomic interval manipulation.

[SnpEff](http://pcingola.github.io/SnpEff/) | Variant annotation and effect prediction.

[Pisces](https://github.com/Illumina/Pisces) | Variant caller optimized for amplicon sequencing.

[Annovar](https://annovar.openbioinformatics.org/en/latest/) | Variant annotation tool.

Please follow the official installation instructions for each tool required for your needs to ensure proper setup.

---

## Contributing

Contributions are welcome! Please open issues or pull requests.

---

Currently in development. See the project documentation at [readthedocs](https://ngs-analyzer.readthedocs.io/en/latest/).
