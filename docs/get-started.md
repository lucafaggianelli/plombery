## Prerequisites

To run Plombery you only need Python (v3.8 or later), if you don't have it installed yet, go
to the [official Python website](https://www.python.org/downloads/), download it
and install it.

## Installation

It's a good practice to install dependencies specific to a project in
a dedicated virtual environment for that project.

Many code editors (IDE) provide their own way to create virtual environments,
otherwise you can use directly the shell typing the following commands.

Create a virtual enrivonment:

```bash
# Run this in your project folder
python -m venv .venv
```

Activate it:
```bash
# on Mac/Linux
source .venv/bin/activate
```

```sh
# on Win
.venv/Script/activate
```

Then install the library:

```sh
pip install plombery
```

Now you're ready to write your first pipeline!
