# Workflows

## add-labels-standardized.yaml

When issues are opened,
this action adds appropriate labels to the issue.
(e.g. "triage", "customer-submission")

- [Add Labels Standardized GitHub Action]
  - Uses: [senzing-factory/build-resources/.../add-labels-to-issue.yaml]

## add-to-project-garage-dependabot.yaml

When a Dependabot Pull Request (PR) is made against `main` branch,
this action adds the PR to the "Garage" project board as "In Progress".

- [Add to Project Garage Dependabot GitHub Action]
  - Uses: [senzing-factory/build-resources/.../add-to-project-dependabot.yaml]

## add-to-project-garage.yaml

When an issue is created,
this action adds the issue to the "Garage" board as "Backlog".

- [Add to Project Garage GitHub Action]
  - Uses: [senzing-factory/build-resources/.../add-to-project.yaml]

## bandit.yaml

When a Pull Request (PR) is made against `main` branch,
this action runs [Bandit] to detect security issues.

- [bandit.yaml]
  - Uses: [lukehinds/bandit-action]

## black.yaml

When a change is committed to GitHub or a Pull Request is made against the `main` branch,
this action runs the [Black] code formatter.

- [black.yaml]

## dependabot-approve-and-merge.yaml

When a Dependabot Pull Request (PR) is made against the `main` branch,
this action determines if it should be automatically approved and merged into the `main` branch.
Once this action occurs [move-pr-to-done-dependabot.yaml] moves the PR on the "Garage" project board to "Done".

- [Dependabot Approve and Merge GitHub Action]
  - Uses: [senzing-factory/build-resources/.../dependabot-approve-and-merge.yaml]

## dependency-scan.yaml

When a Pull Request is made against the `main` branch,
this action runs [Fast Python Vulnerability Scanner] and [pip-audit].

- [dependency-scan.yaml]
  - Uses:
    - [Fast Python Vulnerability Scanner]
    - [pypa/gh-action-pip-audit]

## docker-build-container.yaml

When a Pull Request is made against the `main` branch,
this action verifies that the `Dockerfile` can be successfully built.

_Note:_ The Docker image is **not** pushed to [DockerHub].

- [Docker Build Container GitHub Action]
  - Uses: [senzing-factory/github-action-docker-buildx-build]

## docker-push-containers-to-dockerhub.yaml

After a [Semantic Version] release is created,
this action builds Docker images on multiple architectures and pushes the Docker images to [DockerHub].

- [Docker Push Containers to DockerHub GitHub Action]
  - Uses: [senzing-factory/github-action-docker-buildx-build]

## flake8.yaml

When a change is committed to GitHub or a Pull Request is made against the `main` branch,
this action runs [flake8] for Python style enforcement.

- [flake8.yaml]
  - Uses: [py-actions/flake8]

## isort.yaml

When a change is committed to GitHub or a Pull Request is made against the `main` branch,
this action runs [isort] to sort the Python import statements

- [isort.yaml]
  - Uses: [isort/isort-action]

## lint-workflows.yaml

When a change is committed to GitHub or a Pull Request is made against the `main` branch,
this action runs [super-linter] to run multiple linters against the code.

- [Lint Workflows GitHub Action]
  - Configuration:
    - [.checkov.yaml]
    - [.jscpd.json]
    - [.yaml-lint.yml]
  - Uses: [senzing-factory/build-resources/.../lint-workflows.yaml]

## move-pr-to-done-dependabot.yaml

When a Pull Request is merged into the `main` branch,
this action moves the PR on the "Garage" project board to "Done".

- [Move PR to Done Dependabot GitHub Action]
  - Uses: [senzing-factory/build-resources/.../move-pr-to-done-dependabot.yaml]

## mypy.yaml

When a change is committed to GitHub or a Pull Request is made against the `main` branch,
this action runs [mypy] to perform static type checking.

- [mypy.yaml]

## pylint.yaml

When a change is committed to GitHub,
this action runs [pylint] to perform static code analysis.

- [pylint.yaml]

## pytest-darwin.yaml

When a Pull Request is merged into the `main` branch,
this action runs [pytest] on the Darwin/macOS platform to perform unit tests and code coverage.

- [pytest-darwin.yaml]
  - Uses:
    - [actions/checkout]
    - [actions/setup-python]
    - [senzing-factory/github-action-install-senzing-sdk]
    - [pytest]
    - [actions/upload-artifact]

## pytest-linux.yaml

When a change is committed to GitHub or a Pull Request is made against the `main` branch,
this action runs [pytest] on the Linux platform to perform unit tests and code coverage.

- [pytest-linux.yaml]
  - Uses:
    - [actions/checkout]
    - [actions/setup-python]
    - [senzing-factory/github-action-install-senzing-sdk]
    - [pytest]
    - [actions/upload-artifact]

## pytest-windows.yaml

When a Pull Request is merged into the `main` branch,
this action runs [pytest] on the Windows platform to perform unit tests and code coverage.

- [pytest-windows.yaml]
  - Uses:
    - [actions/checkout]
    - [actions/setup-python]
    - [senzing-factory/github-action-install-senzing-sdk]
    - [pytest]
    - [actions/upload-artifact]

[.checkov.yaml]: ../linters/README.md#checkovyaml
[.jscpd.json]: ../linters/README.md#jscpdjson
[.yaml-lint.yml]: ../linters/README.md#yaml-lintyml
[actions/checkout]: https://github.com/actions/checkout
[actions/setup-python]: https://github.com/actions/setup-python
[actions/upload-artifact]: https://github.com/actions/upload-artifact
[Add Labels Standardized GitHub Action]: add-labels-standardized.yaml
[Add to Project Garage Dependabot GitHub Action]: add-to-project-garage-dependabot.yaml
[Add to Project Garage GitHub Action]: add-to-project-garage.yaml
[bandit.yaml]: bandit.yaml
[Bandit]: https://bandit.readthedocs.io/en/latest/
[black.yaml]: black.yaml
[Black]: https://github.com/psf/black
[Dependabot Approve and Merge GitHub Action]: dependabot-approve-and-merge.yaml
[dependency-scan.yaml]: dependency-scan.yaml
[Docker Build Container GitHub Action]: docker-build-container.yaml
[Docker Push Containers to DockerHub GitHub Action]: docker-push-containers-to-dockerhub.yaml
[DockerHub]: https://hub.docker.com/
[Fast Python Vulnerability Scanner]: https://github.com/vanschelven/fpvs/
[flake8.yaml]: flake8.yaml
[flake8]: https://flake8.pycqa.org/en/latest/
[isort.yaml]: isort.yaml
[isort]: https://pycqa.github.io/isort/
[isort/isort-action]: https://github.com/isort/isort-action
[Lint Workflows GitHub Action]: lint-workflows.yaml
[lukehinds/bandit-action]: https://github.com/lukehinds/bandit-action
[Move PR to Done Dependabot GitHub Action]: move-pr-to-done-dependabot.yaml
[move-pr-to-done-dependabot.yaml]: move-pr-to-done-dependabotyaml
[mypy.yaml]: mypy.yaml
[mypy]: https://mypy-lang.org/
[pip-audit]: https://github.com/pypa/pip-audit
[py-actions/flake8]: https://github.com/py-actions/flake8
[pylint.yaml]: pylint.yaml
[pylint]: https://pypi.org/project/pylint/
[pypa/gh-action-pip-audit]: https://github.com/pypa/gh-action-pip-audit
[pytest-darwin.yaml]: pytest-darwin.yaml
[pytest-linux.yaml]: pytest-linux.yaml
[pytest-windows.yaml]: pytest-windows.yaml
[pytest]: https://docs.pytest.org/en/stable/
[Semantic Version]: https://semver.org/
[senzing-factory/build-resources/.../add-labels-to-issue.yaml]: https://github.com/senzing-factory/build-resources/blob/main/.github/workflows/add-labels-to-issue.yaml
[senzing-factory/build-resources/.../add-to-project-dependabot.yaml]: https://github.com/senzing-factory/build-resources/blob/main/.github/workflows/add-to-project-dependabot.yaml
[senzing-factory/build-resources/.../add-to-project.yaml]: https://github.com/senzing-factory/build-resources/blob/main/.github/workflows/add-to-project.yaml
[senzing-factory/build-resources/.../dependabot-approve-and-merge.yaml]: https://github.com/senzing-factory/build-resources/blob/main/.github/workflows/dependabot-approve-and-merge.yaml
[senzing-factory/build-resources/.../lint-workflows.yaml]: https://github.com/senzing-factory/build-resources/blob/main/.github/workflows/lint-workflows.yaml
[senzing-factory/build-resources/.../move-pr-to-done-dependabot.yaml]: https://github.com/senzing-factory/build-resources/blob/main/.github/workflows/move-pr-to-done-dependabot.yaml
[senzing-factory/github-action-docker-buildx-build]: https://github.com/senzing-factory/github-action-docker-buildx-build
[senzing-factory/github-action-install-senzing-sdk]: https://github.com/senzing-factory/github-action-install-senzing-sdk
[super-linter]: https://github.com/super-linter/super-linter
