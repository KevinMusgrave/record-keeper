./format_code.sh
python -m unittest discover && \
rm -rfv build/
rm -rfv dist/
rm -rfv record_keeper.egg-info/
python3 setup.py sdist bdist_wheel