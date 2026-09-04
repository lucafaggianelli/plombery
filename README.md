<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![PyPI Version][pypi-shield]][pypi-url]
[![Maintainability][Qlty-shield]][Qlty-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
<h3 align="center">Plombery</h3>

  <p align="center">
    Python task scheduler with a user-friendly web UI
    <br />
    <a href="https://lucafaggianelli.github.io/plombery/"><strong>Official website »</strong></a>
    <br />
    <br />
    <a href="https://github.com/lucafaggianelli/plombery">GitHub</a>
    ·
    <a href="https://github.com/lucafaggianelli/plombery/issues">Report Bug</a>
  </p>
</div>

<!-- ABOUT THE PROJECT -->

## About The Project

Plombery is a simple task scheduler for Python with a web UI and a REST API,
if you need to run and monitor recurring python scripts then it's
the right tool for you!

<figure>
  <img src="https://github.com/lucafaggianelli/plombery/raw/main/docs/assets/images/screenshot.png" alt="Plombery Screen Shot">
</figure>

> This project is at its beginning, so it can be shaped and improved with
> your feedback and help!
> If you like it, star it 🌟! If you want a feature or find a bug, open an issue.

## Features

- ⏰ Task scheduling based on [APScheduler](https://github.com/agronholm/apscheduler) (supports Interval, Cron and Date triggers)
- 💻 Built-in Web interface, no HTML/JS/CSS coding required
- 👩‍💻🐍 Pipelines and tasks are defined in pure Python
- 🎛️ Pipelines can be parametrized via [Pydantic](https://docs.pydantic.dev/)
- 👉 Pipelines can be run manually from the web UI
- 🔐 Secured via OAuth2
- 🔍 Debug each run exploring logs and output data
- 📩 Monitor the pipelines and get alerted if something goes wrong
- 💣 Use the REST API for advanced integrations

When you shouldn't use it:

- you need a lot of scalability and you want to run on a distributed system
- you want a no-code tool or you don't want to use Python

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

[![Python][Python]][Python-url]
[![TypeScript][TypeScript]][TypeScript-url]
[![React][React.js]][React-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## 🚀 Getting Started

Check the 👉 [official website](https://lucafaggianelli.github.io/plombery/)
to get started with Plombery.

## 🎮 Try on GitHub Codespaces

Try Plombery with some demo pipelines on GitHub Codespaces:

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

## 🧐 Show me the code

This is how it looks a minimalist pipeline:

<figure align="center">
  <img src="https://github.com/lucafaggianelli/plombery/raw/main/docs/assets/images/minimal-code.png" alt="Minimal code" width="80%">
  <figcaption>I know you want to see it!</figcaption>
</figure>

<!-- ROADMAP -->

## 🛣 Roadmap

See the [open issues](https://github.com/lucafaggianelli/plombery/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## 👩‍💻 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Development

Plombery uses [uv](https://docs.astral.sh/uv/) for Python and
[pnpm](https://pnpm.io/) for the frontend. You'll need Python 3.10 or newer
(uv installs one for you if you don't have it) and Node 22.12 or newer.

Clone a fork of this repo, then install the Python dependencies — uv creates
the virtual environment for you:

```sh
uv sync
```

The frontend is a React app in `frontend/`, and the Python package serves its
build output, so build it once before running the app:

```sh
cd frontend/
pnpm install
pnpm build
```

Now run the example app, which registers a handful of demo pipelines.
`--reload` restarts Plombery whenever a file changes, and `--reload-dir`
adds the Plombery package itself to what's watched, so editing the library
restarts the app too:

```sh
cd examples/
plombery run --pipelines src --reload --reload-dir ../src
```

Open [http://localhost:8000](http://localhost:8000) and you'll find the demo
pipelines, ready to run.

To work on the frontend, leave that running and start the Vite dev server in
another terminal — it hot-reloads the UI and talks to the API on port 8000:

```sh
cd frontend/
pnpm dev
```

### Documentation

The documentation website is based on MkDocs Material, the source code is in the
`docs/` folder and the config is in the `mkdocs.yml` file.

To run a local dev server, run:

```sh
mkdocs serve
```

### Testing

Tests are based on `pytest`, to run the entire suite just run:

```sh
pytest
```

To run a single file or a single test:

```sh
pytest tests/test_api.py
pytest tests/test_api.py::test_api_list_pipelines
```

To run tests coverage, run:

```sh
coverage run -m pytest
coverage report -m
```

The suite runs on every Python version Plombery supports, 3.10 to 3.14. Lint
and format with:

```sh
flake8
black .
```

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

Project Link: [https://github.com/lucafaggianelli/plombery](https://github.com/lucafaggianelli/plombery)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

Plombery is built on top of amazing techs:

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [Apprise](https://github.com/caronc/apprise)
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [Tremor](https://www.tremor.so/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Star History

<a href="https://star-history.com/#lucafaggianelli/plombery&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=lucafaggianelli/plombery&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=lucafaggianelli/plombery&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=lucafaggianelli/plombery&type=Date" />
  </picture>
</a>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/lucafaggianelli/plombery.svg?style=for-the-badge
[contributors-url]: https://github.com/lucafaggianelli/plombery/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/lucafaggianelli/plombery.svg?style=for-the-badge
[forks-url]: https://github.com/lucafaggianelli/plombery/network/members
[stars-shield]: https://img.shields.io/github/stars/lucafaggianelli/plombery.svg?style=for-the-badge
[stars-url]: https://github.com/lucafaggianelli/plombery/stargazers
[issues-shield]: https://img.shields.io/github/issues/lucafaggianelli/plombery.svg?style=for-the-badge
[issues-url]: https://github.com/lucafaggianelli/plombery/issues
[license-shield]: https://img.shields.io/github/license/lucafaggianelli/plombery.svg?style=for-the-badge
[license-url]: https://github.com/lucafaggianelli/plombery/blob/master/LICENSE
[product-screenshot]: images/screenshot.png
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=yellow
[Python-url]: https://www.python.org/
[TypeScript]: https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white
[TypeScript-url]: https://www.typescriptlang.org/
[pypi-shield]: https://img.shields.io/pypi/v/plombery.svg?style=for-the-badge
[pypi-url]: https://pypi.python.org/pypi/plombery
[Qlty-shield]: https://qlty.sh/gh/lucafaggianelli/projects/plombery/maintainability.svg
[Qlty-url]: https://qlty.sh/gh/lucafaggianelli/projects/plombery
