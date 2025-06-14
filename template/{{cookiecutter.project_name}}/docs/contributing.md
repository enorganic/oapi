# Contributing to oapi

Please note that you must have [hatch](https://hatch.pypa.io/latest/)
installed prior to performing the following steps.

## For Contributors and Code Owners

1.  Clone and Install

    To install this project for development of *this library*,
    clone this repository (replacing "~/Code", below, with the directory
    under which you want your project to reside), then run `make`:

    ```bash
    cd ~/Code && \
    git clone\
    {{cookiecutter.repository_url}}.git {{cookiecutter.project_name}} && \
    cd {{cookiecutter.project_name}} && \
    make
    ```

2.  Create a new branch for your changes (replacing "descriptive-branch-name"
    with a *descriptive branch name*):

    ```bash
    git branch descriptive-branch-name
    ```

3. Make some changes.
4. Format and lint your code:

    ```bash
    make format
    ```

5. Test your changes:

    ```bash
    make test
    ```

6. Push your changes and create a pull request.

## For Everyone Else

If you are not a contributor on this project, you can still create pull
requests, however you will need to fork this project, push changes
to your fork, and create a pull request from your forked repository.
