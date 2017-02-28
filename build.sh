#! /bin/bash
set -eu

# TODO: inject ${VERSION} into setup.py somehow
VERSION=${CIRCLE_BUILD_NUM-unknown}
QUARTIC_DOCKER_REPOSITORY=${QUARTIC_DOCKER_REPOSITORY-quartic}

# NOTE: assumes that we've already started the virtualenv

docker build -t ${QUARTIC_DOCKER_REPOSITORY}/formistry:${VERSION} .
docker push ${QUARTIC_DOCKER_REPOSITORY}/formistry:${VERSION}
