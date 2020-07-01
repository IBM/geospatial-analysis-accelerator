# Start from a core stack version
FROM jupyter/scipy-notebook:latest
# Install from requirements.txt file
COPY requirements-pip.txt /tmp/
RUN pip install --requirement /tmp/requirements-pip.txt
COPY requirements-conda.txt /tmp/
RUN conda install --yes --file /tmp/requirements-conda.txt