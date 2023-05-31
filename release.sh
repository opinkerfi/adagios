#!/bin/bash
# Use this script to release a new version of ${project_name}

# Extract current version information
project_name=$(ls *spec | sed 's/.spec$//')
current_version=$(grep ^Version: $project_name.spec | awk '{ print $2 }')
current_release=$(grep "define release" $project_name.spec | awk '{ print $3 }')

UPDATE_INFO_FILE=$(mktemp)
trap "rm -f ${UPDATE_INFO_FILE}" EXIT

if [ -z "$EDITOR" ]; then
    EDITOR=vi
fi

if [ -z $BASH ]; then
    echo "You need /bin/bash to run this script"
    exit 1
fi

main() {

    update_changes || echo FAIL

    update_version_number || echo FAIL

    update_release_number || echo FAIL

    update_debian_changelog || echo FAIL

    new_version=$(grep ^VERSION Makefile | awk '{ print $3 }')

    git_commit || echo FAIL

    git_push || echo FAIL

    upload_to_pypi || echo FAIL

    echo "### All Done"
}



update_changes() {
    ask "Update Changelog?" || return 0
    ${EDITOR} CHANGES || return 1
}


upload_to_pypi() {
    ask "Upload to pypi?" || return 0
    python setup.py build sdist upload || return 1
}

git_push() {
    ask "Upload to github?" || return 0
    git push origin master || return 1
    git push --tags origin master || return 1
}


update_version_number() {
    ask "Update version number?" || return 0
    echo    "Current version is: ${current_version}"
    read -p "New version number: " new_version
    echo
    echo "### Updating Makefile"
    sed -i '' "s/^VERSION.*=.*/VERSION		= ${new_version}/" Makefile
    echo "### Updating ${project_name}/__init__.py"
    sed -i '' "s/^__version__.*/__version__ = '${new_version}'/" ${project_name}/__init__.py
    echo "### Updating ${project_name}.spec"
    sed -i '' "s/^Version: ${current_version}/Version: ${new_version}/" ${project_name}.spec
    echo "### Updating rel-eng/packages/${project_name}"
    echo "${new_version}-${current_release} /" > rel-eng/packages/${project_name}
}

update_release_number() {
    ask "Update release number?" || return 0
    echo    "Current release is: ${current_release}"
    read -p "New release number: " new_release
    echo
    echo "### Updating Makefile"
    sed -i '' "s/^RELEASE.*=.*/RELEASE		= ${new_release}/" Makefile
    echo "### Updating ${project_name}.spec"
    sed -i '' "s/^%define release ${current_release}/%define release ${new_release}/" ${project_name}.spec
    echo "### Updating rel-eng/packages/${project_name}"
    #echo "${new_version}-${current_release} /" > rel-eng/packages/${project_name}
    echo "${new_version}-${new_release} /" > rel-eng/packages/${project_name}
}

update_debian_changelog() {
    echo "### Updating debian.upstream/changelog"
    DATE=$(LANG=C date -R)
    NAME=$(git config --global --get user.name)
    MAIL=$(git config --global --get user.email)
    changelog=$(mktemp)
    echo "${project_name} (${new_version}-${new_release}) unstable; urgency=low" > ${changelog}
    echo "" >> ${changelog}
    echo "  * New upstream version" >> ${changelog}
    echo "" >> ${changelog}
    echo " -- ${NAME} <${MAIL}>  ${DATE}" >> ${changelog}
    echo "" >> ${changelog}
    cat debian.upstream/changelog >> ${changelog}
    cp -f ${changelog} debian.upstream/changelog
}


git_commit() {
    ask "Commit changes to git and tag release ?" || return 0
    git commit Makefile CHANGES ${project_name}/__init__.py rel-eng/packages/${project_name} ${project_name}.spec debian.upstream/changelog -m "Bumped version number to $new_version" > /dev/null
    git tag ${project_name}-${new_version}-${new_release} -a -m "Bumped version number to $new_version-$new_release"
}

ask() {
    read -n 1 -p "### $@ [Yn] "
    echo
    if [[ $REPLY =~ n ]]; then
        return 1
    else
        return 0
    fi
}

main;

# vim: sts=4 expandtab autoindent
