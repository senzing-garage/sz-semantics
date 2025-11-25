# Linters

## .jscpd.json

- [.jscpd.json]
- Used by [lint-workflows.yaml]
- [jscpd]
  - [jscpd configuration]
  - Example:

    ```json
    {
      "ignore": ["**/*.go,**/go-test*.yaml"],
      "threshold": 10
    }
    ```

## .yaml-lint.yml

- [.yaml-lint.yml]
- Used by [lint-workflows.yaml]
- [yaml-lint]
  - [yaml-lint configuration]

[.jscpd.json]: .jscpd.json
[.yaml-lint.yml]: .yaml-lint.yml
[jscpd configuration]: https://github.com/kucherenko/jscpd/tree/master/apps/jscpd#options
[jscpd]: https://github.com/kucherenko/jscpd
[lint-workflows.yaml]: ../workflows/README.md#lint-workflowsyaml
[yaml-lint configuration]: https://yamllint.readthedocs.io/en/stable/configuration.html
[yaml-lint]: https://github.com/adrienverge/yamllint
