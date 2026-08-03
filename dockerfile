FROM ubuntu:latest

# Base tools jobtracker's install flow needs: curl for `curl | bash` + uv's own installer,
# ca-certificates for HTTPS, python3 as a baseline interpreter. wget/ping/nano kept for general
# container usability.
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    iputils-ping \
    nano \
    ca-certificates \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Node via NodeSource's own setup script, not the default `apt install nodejs` package -- Debian/
# Ubuntu's nodejs package does NOT bundle npm (a separate apt package, easy to miss), which silently
# breaks `npx jobtracker-agents` with no clear error until you check `which npx`. NodeSource's
# package bundles node+npm+npx together correctly in one shot.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
