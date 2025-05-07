FROM python:3.10-slim

# Install dependencies
RUN apt update && apt install -y git libssl-dev libffi-dev build-essential

# Clone the Cowrie repository
RUN git clone https://github.com/cowrie/cowrie.git /opt/cowrie

# Set working directory
WORKDIR /opt/cowrie

# Install Python requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the default configuration from correct directory
RUN cp etc/cowrie.cfg.dist etc/cowrie.cfg

# Create cowrie user and change ownership
RUN useradd -m cowrie
RUN chown -R cowrie:cowrie /opt/cowrie

# Switch to cowrie user
USER cowrie

# Set working directory as cowrie user
WORKDIR /opt/cowrie

# Start Cowrie when the container runs
CMD ["bin/cowrie"]
