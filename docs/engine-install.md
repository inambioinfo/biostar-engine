## Installation

Our installation instructions rely on [conda][conda] though other alternatives are equally viable. Users may use `virtualenv`, `pipenv`, `homebrew`, `apt-get` etc, or they may opt to not using any environment management tool. We use [conda][conda] primarily since it allows us to also manage bioinformatics tools.

### 1\. Create a virtual environment

[conda]: https://conda.io/docs/

    conda create -y --name engine python=3.6
    source activate engine

### 2\. Clone the source server code and the recipe code:

There are different repositories for the engine and the recipes.

    # This repository contains the biostar-engine software that can run recipes.
    git clone https://github.com/biostars/biostar-engine.git

    # This repository stores the various data analysis recipes.
    git clone https://github.com/biostars/biostar-recipes.git

### 3\. Install the python dependencies:

To run the server you will need to install the dependencies:

    # Switch to the biostar-engine directory.
    cd biostar-engine

    # Install server dependencies.
    pip install -r conf/pip_requirements.txt

    # Enable the required channels.
    conda config --add channels r
    conda config --add channels conda-forge
    conda config --add channels bioconda

    # Install the conda requirements.
    conda install --file conf/conda_requirements.txt

At this point the installation is complete.

### 4\. Start the server

All commands run through `make`. To initialize and run the test site use:

      make reset serve

Visit <http://localhost:8000> to see your site running.

The default admin email/password combination is `admin@localhost` for both. Use these to log into the test site as an admin user.

## Bioinformatics environment

To run bioinformatics tools the environment that the jobs are run in needs to be set up appropriately. The instructions makes use of [bioconda][bioconda] to install tools into the current environment. Make sure that you have enabled [bioconda][bioconda] prior to running the following:

    # Activate the environment.
    source activate engine

    # Switch to the engine directory.
    cd biostar-recipes

    # Install the conda dependencies.
    conda install --file conf/conda_requirements.txt

    # Add the recipes to the python path.
    python setup.py develop

[bioconda]: https://bioconda.github.io/



## Deployment

The site is built with Django therefore the official Django documentation applies to maintaining and deploying the site:

* <https://docs.djangoproject.com/>

## Running jobs

A recipe submitted for execution is called a job.

When the job is run the recipe parameters are applied onto recipe template to produce the script that gets executed. This transformation takes place right before executing the job.

Jobs can be executed as commands. See the `job` command for details:

    python manage.py job --help

The command has number of parameters that facilitate job management and recipe development.
For example:

    python manage.py job --list

will list all the jobs in the system. Other flags that allow users to investigate and override the behaviors.

    python manage.py job --id 4 --show_script

will print the script for job 4 that is to be executed to the command line. Other flags such as `-use_template` and `-use_json` allows users to override the data or template loaded into the job.
This can be useful when developing new recipes.

Another handy command:

    python manage.py job --next

will execute the next queued job. The job runner may be run periodically with cron.

## Automatic job spooling

The Biostar Engine supports `uwsgi`. When deployed through
`uwsgi` jobs are queued and run automatically through the `uwsgi` spooler. See the `uwsgi` documentation  for details on how to control and customize that process.

* <https://uwsgi-docs.readthedocs.io/en/latest/>

[uwsgi]: <https://uwsgi-docs.readthedocs.io/en/latest/

## Bioinformatics Recipes

Bioinformatics related recipes are stored and distributed from a separate repository:

* <https://github.com/biostars/biostar-recipes>

## Security considerations

**Note**: The site is designed to execute scripts on a remote server. In addition the site
allows users with **moderator** rights may change the content of these scripts.

It is **extremely important** to monitor, restrict and guard access to all
accounts with moderator privileges!
