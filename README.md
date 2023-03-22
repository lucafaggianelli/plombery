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



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/lucafaggianelli/mario-pype">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Mario Pype</h3>

  <p align="center">
    Python task scheduler with a user-friendly web UI
    <br />
    <a href="https://github.com/lucafaggianelli/mario-pype"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/lucafaggianelli/mario-pype">View Demo</a>
    ·
    <a href="https://github.com/lucafaggianelli/mario-pype/issues">Report Bug</a>
    ·
    <a href="https://github.com/lucafaggianelli/mario-pype/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

Mario Pype is a simple task scheduler for Python with a web UI and a REST API,
if you need to run and monitor recurring python scripts then it's
the right tool for you!

> This project is at its beginning, so it can be shaped and improved with
  your feedback and help!
  If you like it, star it 🌟! If you want a feature or find a bug, open an issue.

Features:
- ⏰ Task scheduing based on APScheduler (supports Interval, Cron and Date triggers)
- 💻 Built-in Web interface, no HTML/JS/CSS coding required
- 👩‍💻🐍 Pipelines and tasks are defined in pure Python
- 👊 Pipelines can be run manually from the web UI
- 🔍 Debug your tasks exploring logs and output data
- 📩 Monitor tasks executions and get alerted if something goes wrong
- 💣 Use the REST API for advanced integrations
- ✨ A lot more features are coming, check the [open issues](https://github.com/lucafaggianelli/mario-pype/issues)!

When you shouldn't use it:
- you need a lot of scalability and you want to run on a distributed system
- you want a no-code tool or you don't want to use Python

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With

* [![Python][Python]][Python-url]
* [![TypeScript][TypeScript]][TypeScript-url]
* [![React][React.js]][React-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

To run Mario Pype you only need Python (v3.8 or later), if you don't have it installed yet, go
to the [official Python website](https://www.python.org/downloads/), download it
and install it.

### Installation

Create and activate a virtual enrivonment, for example:

```sh
python -m venv .venv
# on Mac/Linux
source .venv/bin/activate
# on Win
.venv/Script/activate
```

Then install the library:

> Mario Pype is not published yet on pypi.org, that's why you need to install it
    from git!

```sh
pip install git+https://github.com/lucafaggianelli/mario-pype
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Create your first Pipeline

*Pipelines* are entities that can be scheduled and are composed of 1 or multiple *Tasks*.

A Pipeline is a Python class that contains a list of tasks and eventually a list of triggers:

```py
class DummyPipeline(Pipeline):
    """This is a very useless pipeline"""

    tasks = [fetch_raw_sales_data]

    triggers = [
        Trigger(
            id="daily",
            name="Daily",
            description="Run the pipeline every day",
            aps_trigger=IntervalTrigger(days=1),
        )
    ]
```

A *Task* is the base block in Mario Pype and it's just a Python function that
performs an action.

This is the Task `fetch_raw_sales_data` used in the `DummyPipeline` pipeline ... it doesn't do much,
but it showcase the basics:

```py
@task
async def fetch_raw_sales_data(input_data, params = None):
    logger = get_logger()

    for i in range(10):
        await sleep(1 + np.random.random() / 2)
        logger.debug("I slept for %d s", i)

    sales = pd.DataFrame({
        "price": np.random.randint(1, 1000, 50),
        "store_id": np.random.randint(1, 10, 50),
        "date": datetime.today(),
        "sku": np.random.randint(1, 50, 50)
    })

    return sales
```

Finally register the pipeline so Mario Pype knows it's there:

```py
# app.py
from mario import Mario

app = Mario()

app.register_pipeline(DummyPipeline())
```

### Run Mario Pype

Mario Pype is based on FastAPI so you can run it as a normal FastAPI app via `uvicorn`:

```sh
uvicorn my_project.app:app --reload
```

### Configure notifications

You can optionally configure notifications creating the file `mario.config.yaml`
in the project root:

```yml
notifications:
  - pipeline_status:
      - failed
      - completed
    channels:
      - mailto://myuser:mypass@gmail.com
```

You can have multiple notifications configs and multiple channels for each config.
The channel is a URI directly passed to the notifications engine
[Apprise](https://github.com/caronc/apprise), check their docs for the supported channels.


<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/lucafaggianelli/mario-pype/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

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

Clone a fork of this repo and start your dev environment.

Create a python virtual environment:

```sh
python -m venv .venv
# on Mac/Linux
source .venv/bin/activate
# on Win
.venv/Script/activate
```

and install the dependencies:

```sh
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

for development purposes, it's useful to run the example application:
```sh
cd examples/
export PYTHONPATH=$(pwd)/..
uvicorn dummy.app:app --reload --reload-dir ..
```

The React frontend is in the `frontend/` folder, enter the folder
and install the dependencies:

```sh
cd frontend/
# The project uses yarn as dependency manager, if you don't have
# it, you must install it.
# This command will install the deps:
yarn
```

run the development server:

```sh
yarn dev
```

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/lucafaggianelli/mario-pype](https://github.com/lucafaggianelli/mario-pype)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Mario Pype is built on top of amazing techs:

* [FastAPI](https://fastapi.tiangolo.com/)
* [Pydantic](https://docs.pydantic.dev/)
* [APScheduler](https://apscheduler.readthedocs.io/)
* [Apprise](https://github.com/caronc/apprise)
* [React](https://react.dev/)
* [Vite](https://vitejs.dev/)
* [Tremor](https://www.tremor.so/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/lucafaggianelli/mario-pype.svg?style=for-the-badge
[contributors-url]: https://github.com/lucafaggianelli/mario-pype/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/lucafaggianelli/mario-pype.svg?style=for-the-badge
[forks-url]: https://github.com/lucafaggianelli/mario-pype/network/members
[stars-shield]: https://img.shields.io/github/stars/lucafaggianelli/mario-pype.svg?style=for-the-badge
[stars-url]: https://github.com/lucafaggianelli/mario-pype/stargazers
[issues-shield]: https://img.shields.io/github/issues/lucafaggianelli/mario-pype.svg?style=for-the-badge
[issues-url]: https://github.com/lucafaggianelli/mario-pype/issues
[license-shield]: https://img.shields.io/github/license/lucafaggianelli/mario-pype.svg?style=for-the-badge
[license-url]: https://github.com/lucafaggianelli/mario-pype/blob/master/LICENSE
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=yellow
[Python-url]: https://www.python.org/
[TypeScript]: https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white
[TypeScript-url]: https://www.typescriptlang.org/