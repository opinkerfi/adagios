#!/bin/sh
# Use this script to release a new version of Adagios

current_version=$(grep ^Version: adagios.spec | awk '{ print $2 }')
current_release=$(grep "define release" adagios.spec | awk '{ print $3 }')

echo    "Current version is: $current_version"
echo -n "New version number: "
read new_version

echo new version: $new_version


echo "### Updating version number"
sed -i "s/Version: $current_version/Version: $new_version/" adagios.spec
sed -i "s/__version__=.*/__version__='${new_version}'/" adagios/__init__.py
echo "${new_version}-${current_release} /" > rel-eng/packages/adagios

dch -v "${new_version}" --distribution unstable "New Upstream release"

echo "### commiting and tagging current git repo"
git commit adagios/__init__.py rel-eng/packages/adagios adagios.spec debian.upstream/changelog -m "Bumped version number to $new_version" > /dev/null
git tag adagios-${new_version}-${current_release} -a -m "Bumped version number to $new_version" 

# The following 2 require access to git repositories and pypi
echo "### Pushing commit to github"
git push origin master || exit 1
git push --tags origin master || exit 1
echo "Building package and uploading to pypi"
python setup.py build sdist upload || exit 1
