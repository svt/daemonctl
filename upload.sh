./bumpversion.py --$1 || exit 1
python setup.py sdist upload -r internal
if [ "$1" == "release" ]; then
./bumpversion.py --patch
fi

