# Contributing to Plombery

Welcome to Plombery! We're thrilled that you're interested in contributing.

Before you get started, please read and follow these guidelines to ensure a smooth and collaborative contribution process.

## Table of Contents

- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)
- [Questions](#questions)
- [License](#license)

## How Can I Contribute?

There are several ways you can contribute to this project:

- Reporting bugs
- Suggesting new features or enhancements
- Fixing bugs or implementing new features by creating pull requests
- Improving documentation
- Helping others by responding to questions and issues

## Getting Started

### Prerequisites

Tools requierd to run Plombery:

- Python3 (Version: >=3.x)
- Pip
- Yarn (for frontend)

### Setup

1. Fork the repository and clone it to your local machine.

2. Create a python virtual environment:

```sh
> python3 -m venv .venv
> source .venv/bin/activate # on Mac/Linux
> .venv/Script/activate # on Win
```

3. install dependencies:

```sh
pip install .
```

4. Duplicate the `.example.env` to `.env` and update the variables accordingly.

5. The React frontend is in the `frontend/` folder, enter the folder and install the dependencies:

```sh
> cd frontend
> yarn
```

- run the development server:

```sh
yarn dev
```

6. For development purposes only,open a new terminal and run the example backend/API:

```sh
cd examples

# Create a venv for the example app
> python3 -m venv .venv-example
> source .venv-example/bin/activate
> pip install -r requirements.txt

> ./run.sh # or ./run.ps1 for win
```

## Development Workflow

1. Fork the Project
2. Create your feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'your-commit-msg-here'`)
4. Push your branch to your fork: `git push origin feature/your-feature-name`.
5. Create a pull request (PR) to the project's repository.

## Submitting a Pull Request

- Provide a descriptive title for your PR.
- Explain the purpose and context of your changes.
- Mention any issues that your PR addresses or closes.

## Reporting Bugs

If you encounter a bug or unexpected behavior, please follow these steps:

1. Check the [GitHub issue tracker](https://github.com/lucafaggianelli/plombery/issues) to see if the issue has already been reported.
2. If not, create a new issue and provide detailed information about the problem.
3. Include any error messages, logs, or screenshots that may be helpful for debugging.
4. Be clear and concise in your description.

## Feature Requests

If you have an idea for a new feature or enhancement, please follow these steps:

1. Check the [GitHub issue tracker](https://github.com/lucafaggianelli/plombery/issues) to see if the feature request already exists.
2. If not, create a new issue and provide a clear description of the feature or enhancement you'd like to see.
3. (optional) Include any use cases or examples to illustrate the feature's utility.

## Questions

If you have questions or need assistance, you can ask for help by:

- Creating a new issue in the GitHub issue tracker.

## License

By contributing to this project, you agree that your contributions will be licensed under the [MIT license](https://github.com/lucafaggianelli/plombery/blob/main/LICENSE).

Thank you for contributing to Plombery.
