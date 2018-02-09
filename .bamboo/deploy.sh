set -eu
export HOME=${bamboo_PRODUCTION_HOME}
export PATH=/shared/utils.x86_64/anaconda2-4.3.1/bin:$PATH
export CONDA_PATH_BACKUP=${CONDA_PATH_BACKUP:-$PATH}
export CONDA_PREFIX=${CONDA_PREFIX:-}
export CONDA_PS1_BACKUP=${CONDA_PS1_BACKUP:-}
conda remove -y -${bamboo_VERBOSITY} --prefix ${bamboo_NEXT_PRODUCTION_ENVIRONMENT} --all
conda create -y -${bamboo_VERBOSITY} -c defaults --clone ${bamboo_BASE_ENVIRONMENT} --prefix ${bamboo_NEXT_PRODUCTION_ENVIRONMENT}
source activate ${bamboo_NEXT_PRODUCTION_ENVIRONMENT}
conda install -y -${bamboo_VERBOSITY} -c conda-forge opencv
conda install -y -${bamboo_VERBOSITY} -c anaconda gcc
files=( artifacts/*.whl )
pip install ${files[0]}
source deactivate
chmod -R 777 ${bamboo_NEXT_PRODUCTION_ENVIRONMENT}