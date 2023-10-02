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

## 🎮 Try on GitHub Codespaces

If you don't want to setup the project locally and you just want to have a look at
Plombery and how it works, then you should try GitHub Codespaces:

<figure align="center">
  <img src="https://github.com/lucafaggianelli/plombery/raw/main/docs/assets/images/codespaces.png" alt="Get Started on Codespaces">
</figure>

Codespaces are development environments that run in the cloud so you
can run a project without cloning it, installing deps etc, here's an how
to:

- Go to the the [lucafaggianelli/plombery](https://github.com/lucafaggianelli/plombery) GitHub page
- Click on the green **Code** button on the top right
- Choose the **Codespaces** tab
- Click on *create new codespace from main* or reuse an existing one
- A new page will open at `github.dev`, wait for the environment build
- Once your codespace is ready you'll see an interface similar to VSCode
- Some commands will be run in the terminal to build the frontend etc., wait for their completion
- If everything went well, Plombery home page will be open in a new browser tab
- Changes in the Python code will be immediately reflected in the web page, like if you were developing
  on your laptop
