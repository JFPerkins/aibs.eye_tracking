set -eu
export PATH=/shared/utils.x86_64/anaconda2-4.3.1/bin:$PATH
export TMPDIR=${bamboo.build.working.directory}/.tmp
export CONDA_PATH_BACKUP=${CONDA_PATH_BACKUP:-$PATH}
export CONDA_PREFIX=${CONDA_PREFIX:-}
export CONDA_PS1_BACKUP=${CONDA_PS1_BACKUP:-}
source activate ${bamboo.build.working.directory}/.conda/${bamboo_TEST_ENVIRONMENT}
cd ${bamboo.CHECKOUT_DIRECTORY}
python setup.py bdist_wheel
source deactivate
