# template

A [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/) template is
provided to kickstart authoring of your `oapi` client/SDK:

-   Install [hatch](https://hatch.pypa.io/latest/install/)

-   Install [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/installation.html)

-   Execute the following command (replacing "~/Code" with the path under
    which you want to create your new project):

    ```bash
    cd ~/Code && \
    cookiecutter "https://github.com/enorganic/oapi.git" --directory="template"
    ```

-   Follow the prompts to enter template fields. For example:

    ```console
    $ cookiecutter "https://github.com/enorganic/oapi.git" --directory="template"
    You've downloaded /Users/nonsense/.cookiecutters/oapi/template before. Is it okay to delete and re-download it? [y/n] (y): y
    [1/9]  project_name - The name of your project (example: namespace-application-sdk) (): my-test-sdk
    [2/9] package - The module path of your base package, including namespacing, if applicable (example: enterprise_name.application_client) (oapi_test_client): 
    [3/9] package_directory - The relative file path to your base package (example: src/enterprise_name/application_client) (src/oapi_test_client): 
    [4/9] author_email (): info@nonsense.org
    [5/9] repository_url (): https://github.com/your-organization/my-test-sdk
    [6/9] documentation_url (): https://your-organization.github.io/my-test-sdk
    [7/9] openapi_document_url - The URL from which an OpenAPI document for this client can be obtained (example: https://raw.githubusercontent.com/cloudflare/api-schemas/refs/heads/main/openapi.json) (): https://raw.githubusercontent.com/cloudflare/api-schemas/refs/heads/main/openapi.json
    [8/9] openapi_git_repository_url - The URL of the Git repository containing the Open API document (example: https://github.com/cloudflare/api-schemas.git) (): 
    [9/9] openapi_git_repository_document_path - The relative path to the OpenAPI document in the repository (example: openapi.json) ():
    ```

    The resulting directory/file structure created by the above example input
    looks as follows:

    ```console
    $ tree -a -I '.git|.mypy_cache|.ruff_cache' my-test-sdk 
    my-test-sdk
    ├── .editorconfig
    ├── .github
    │   └── workflows
    │       ├── distribute.yml
    │       └── test.yml
    ├── .gitignore
    ├── docs
    │   ├── api
    │   │   ├── oapi_test_client.client.md
    │   │   └── oapi_test_client.model.md
    │   ├── assets
    │   │   ├── javascripts
    │   │   │   └── extra.js
    │   │   └── stylesheets
    │   │       └── style.css
    │   ├── CNAME
    │   ├── contributing.md
    │   └── index.md
    ├── Makefile
    ├── mkdocs.yaml
    ├── openapi
    │   ├── fixed.json
    │   └── original.yaml
    ├── pyproject.toml
    ├── README.md
    ├── scripts
    │   └── remodel.py
    ├── src
    │   └── oapi_test_client
    │       ├── client.py
    │       └── model.py
    └── tests
        ├── conftest.py
        └── test_integration.py
    ```

-   Once you've created your new project, you will want to start by
    editing `scripts/remodel.py` (read the inline comments for instruction).
    Once you've edited this as needed, run
    `cd my-test-sdk && make remodel` to generate
    your model and client modules.

-   Edit `tests/conftest.py` such that `get_client` returns a client
    connecting to a suitable instance of the API against which to perform
    integration tests.

-   Author your integration tests in `tests/test_integration.py`
    (read inline comments for instruction).

-   Run `make test` to execute your tests. When/if validation errors are
    raised for API responses, edit the `fix_openapi` function in
    `scripts/remodel.py` to fix the OpenAPI document such that it correctly
    represents the data returned. For perfect Open API documents, this
    step will not be necessary, but candidly I've found precious few *perfect*
    Open API documents in the wild :-).

-   You will first need to create your repository on Github:
    `https://github.com/organizations/your-organization/repositories/new`
    (replace "your-organization" with your organization, of course)

-   Initialize and configure your repository locally. For the project created
    in our preceding examples, those commands would be:

    ```bash
    git init && \
    git add . && \
    git stage . && \
    git commit -m "First Commit" && \
    git remote add origin "https://github.com/your-organization/my-test-sdk.git"
    ```
