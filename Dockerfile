# Start from a core stack version
FROM jupyter/datascience-notebook:latest
# Install from requirements.txt file
COPY requirements-pip.txt /tmp/
RUN pip install --requirement /tmp/requirements-pip.txt