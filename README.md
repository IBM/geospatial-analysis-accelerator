# Geospatial Analysis Accelerator
The objective of this repository is to:

>Identify, demonstrate and create assets that can be used by Data Scientists to speed up their geospatial analysis.

These assets are the result of an research initiative started by the [IBM Academy of Technology](https://www.ibm.com/blogs/academy-of-technology/{target='_blank'}). The intend is to extend and grow the number & maturity of assets over time.

The background of the IBM AoT Study and the first Use Case is described in two LinkedIn articles:

- [Accelerate analyzing the influence of regional factors on COVID-19 using IBM PAIRS & Jupyter Notebooks](https://www.linkedin.com/pulse/accelerate-analyzing-influence-regional-factors-using-marc-fiammante/)
- [Spearman correlations between the UV Index and COVID-19 per region using IBM PAIRS & Jupyter Notebooks](https://www.linkedin.com/pulse/spearman-correlations-between-uv-index-covid-19-per-mazin-phd-mmt)

This repository will hold the assets supporting that initiative. 

NB: the exploration is only to identify & create assets for data scientists to explore geospatial-temporal data. Examples provided with the assets **should not** be taken as any interpretation of the results. We are not trained epidemiologists and therefore leave all interpretations to those that have the professional expertise.

## COVID-19 Geospatial Correlation
The first asset is a [Jupyter Notebook](https://jupyter.org/) that can be used to determine [Spearman's rank correlation coefficient](https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient) or a [log-linear generalized additive model (GAM)](https://en.wikipedia.org/wiki/Generalized_additive_model) between COVID-19 cases and Geospatial & Temporal information out of [IBM PAIRS Geoscope](https://ibmpairs.mybluemix.net/).

The [COVID-19 Geospatial Correlation Notebook](https://github.com/ibm/geospatial-analysis-accelerator/notebooks/COVID-19_Geospatial_Correlation.ipynb) can be used in a existing Juyter Notebook server, provided that Python 3.x is used and the required packages are installed via pip and conda.

The second option is to use the provided Dockerfile to build a Docker image. To use this option you require a Docker environment, e.g. by installing [Docker Desktop](https://www.docker.com/products/docker-desktop).

Then you need to build the Docker Image:

1. Clone this repository and use a terminal to navigate to the cloned directory.

2. Build the Docker Image:
    ```
    docker build --rm -t ibm/geospatial-analysis-accelerator .
    ```
3. Start the Docker Image & Mount the current directory:

    On Linux & Mac:
    ```
    docker run -it --rm -v $(pwd):/home/jovyan/work -p 8888:8888 ibm/geospatial-analysis-accelerator
    ```
    On Windows via cmd:
    ```
    docker run -it --rm -v "%cd%":/home/jovyan/work -p 8888:8888 ibm/geospatial-analysis-accelerator
    ```
    On Windows via Powershell:
    ```
    docker run -it --rm -v ${pwd}:/home/jovyan/work -p 8888:8888 ibm/geospatial-analysis-accelerator
    ```

    This will start the Jupyter Notebook server and mount the current directory.
    
    The Jupyter Notebook server will be available on http://127.0.0.1:8888/ with the access token listed in the console.

The Notebook is available in the *notebooks* directory and contains full documentation on how to use the Notebook.

## IBM PAIRS
If you don't have access to the IBM PAIRS API, then you can request accesss via the [IBM PAIRS Access procedure](IBMPAIRS-Access.md).

If you want to get started without API access you can ! This repo contains an [IBM PAIRS Local Cache file for The Netherlands](/data/NL/IBMPAIRS_LocalCache.csv).

The file contains a small set of data:
- *geospatial filter*: NL
- *temporal filter*: February 13 2020 - June 19 2020
- *data filter*: IBM TWC (UV Index, Temperature Above Ground, Relative Humidity, Wind Speed).
- *aggregation*: daily by region code 

This small set of data is sufficient to run the COVID-19 Geospatial Correlation Notebook, but true value comes with access to the IBM PAIRS API.

The data in this IBM PAIRS Local Cache File is made available under [CDLA-Sharing-1.0](https://cdla.io/sharing-1-0/)
