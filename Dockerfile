FROM renovate/renovate:37.153
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv $HOME/.local/bin/uv /usr/local/bin/uv
