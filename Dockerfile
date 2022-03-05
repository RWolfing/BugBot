# NB! when updating make sure the version is in sync with:
# * rasa version in requirements.txt
# * RASA_VERSION and RASA_X_VERSION  in .github/workflows/continuous-deployment.yml
# Pull SDK image as base image
FROM rasa/rasa-sdk:latest

# Copy actions requirements
# Copy actions code to working directory
COPY ./actions /app/actions
COPY actions/requirements-actions.txt /app

# Change to root user to install dependencies
USER root

RUN apt-get update -qq && \
  apt-get install -y --no-install-recommends \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  # required by psycopg2 at build and runtime
  libpq-dev \
  # required for health check
  curl \
  && apt-get autoremove -y
  
# Make sure that all security updates are installed
RUN apt-get update && apt-get dist-upgrade -y --no-install-recommends

# Install extra requirements for actions code
RUN pip install --no-cache-dir -r requirements-actions.txt

# Don't use root user to run code
USER 1001

# Start the action server
CMD ["start", "--actions", "actions.actions"]
