# Docker API

## DockerSandbox

::: pydantic_ai_backends.backends.docker.sandbox.DockerSandbox
    options:
      show_root_heading: true
      members:
        - __init__
        - runtime
        - session_id
        - execute
        - read
        - write
        - ls_info
        - glob_info
        - grep_raw
        - start
        - stop
        - is_alive

## BaseSandbox

::: pydantic_ai_backends.backends.docker.sandbox.BaseSandbox
    options:
      show_root_heading: true
      members:
        - __init__
        - id
        - execute
        - ls_info
        - read
        - write
        - edit
        - glob_info
        - grep_raw

## SessionManager

::: pydantic_ai_backends.backends.docker.session.SessionManager
    options:
      show_root_heading: true
      members:
        - __init__
        - get_or_create
        - release
        - cleanup_idle
        - start_cleanup_loop
        - shutdown
        - sessions
        - session_count

## RuntimeConfig

The runtime descriptor (image, setup commands, environment) used by
[`DockerSandbox`][pydantic_ai_backends.DockerSandbox] and the session manager is
documented in the type reference: [`RuntimeConfig`][pydantic_ai_backends.types.RuntimeConfig].

## Built-in Runtimes

```python
from pydantic_ai_backends import BUILTIN_RUNTIMES

# Available runtimes
print(BUILTIN_RUNTIMES.keys())
# dict_keys(['python-minimal', 'python-datascience', 'python-web', 'node-minimal', 'node-react'])

# Use a runtime
from pydantic_ai_backends import DockerSandbox
sandbox = DockerSandbox(runtime="python-datascience")
```

| Runtime | Base Image | Packages |
|---------|------------|----------|
| `python-minimal` | python:3.12-slim | (none) |
| `python-datascience` | python:3.12-slim | pandas, numpy, matplotlib, scikit-learn, seaborn |
| `python-web` | python:3.12-slim | fastapi, uvicorn, sqlalchemy, httpx |
| `node-minimal` | node:20-slim | (none) |
| `node-react` | node:20-slim | typescript, vite, react, react-dom, @types/react |
