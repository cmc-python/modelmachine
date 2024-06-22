# Development

This project uses [hatch](https://hatch.pypa.io/latest/) for building.


## Install latest development version
```shell
pip install git+https://github.com/cmc-python/modelmachine.git@main
```

## Local environment
For local development hatch will create virtualenv and
install package with dependencies for you.
```shell
git clone https://github.com/cmc-python/modelmachine.git
cd modelmachine
ln -s $(pwd)/.githooks/* .git/hooks
pip install hatch
hatch shell
```
Now you are in local environment and command `modelmachine` is accessable

## Test
Test local version:
```shell
hatch test
```

Show coverage:
```shell
hatch test --cover
```

### Linting
```
hatch fmt
```

## Publish
Publishing hhappens automatically by github actions.
To publish new version, create a release tag and release itself in github
web interface.
