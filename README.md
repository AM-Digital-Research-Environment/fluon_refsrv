# Services for Fluid Ontologies

This flask application provides services for integrating Fluid Ontologies into WissKI.

It contains two APIs for management of data, and provision of data to external consumers.
A frontend for monitoring interactions is also available.

## Development

**Do not use `pip install` or `pip install -r requirements.**
This project uses [poetry](https://python-poetry.org/) to manage dependencies, so you need to install poetry on your system first.
It should auto-detect the virtual environment you'll create in the next steps.

1. Create a virtual environment in the root of this repo, and activate it:
   ```shell
    $ python -m venv venv
    $ source venv/bin/activate
   ```
2. Pull in all dependencies, including dev-dependencies:
   ```shell
   $ poetry install
   ```

That should be it.

### Adding dev-dependencies

In order to add development dependencies such as linters, provide the `dev`-group to poetry:

``` shell
$ poetry add pytest --group dev
```

### Adding dependencies

In order to add root dependencies required for main functionality:

``` shell
$ poetry add pytest
```

## Deployment

* use [dmkg/fo_training](https://gitlab.uni-bayreuth.de:dmkg/fo_training) to train models for recommendation

## Next Steps

Right now, this is a working base version which has room for improvements.

### Obtaining Recommendations for Known Users

Right now, this reports a simple list of items ordered by ranking from the database.
Maybe this can be adjusted by offering cluster/group assignments of items to the frontend as well.

### Obtaining Recommendations for New Users

New users just get to see the list of most average cluster items.
Can this be done better/different?
