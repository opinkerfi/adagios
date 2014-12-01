#!/bin/bash
BRANCH_DIR="/var/www/html/branches"
TMP_DIR=`mktemp -d`
GITHUB_REPO="https://github.com/opinkerfi/adagios.git"
LOCAL_REPO="/var/www/html/adagios.git"
APACHE_CONFDIR="/etc/httpd/conf.d/adagios/"
MASTER_APACHE_CONFIG="/etc/httpd/conf.d/adagios.conf"

mkdir -p $BRANCH_DIR


clean_apache_configuration() {
  mkdir -p $APACHE_CONFDIR
  rm -f "$APACHE_CONFDIR/*.conf"
}

error() {
  echo Error: $@
  exit 1
}

add_link_to_index_page() {
  local branch_name="$1"
  test -z $branch_name && error "please use arguments when calling create_apache_config_for_branch"
  
  cd $TMP_DIR/branches/$branch_name
  local git_log=`git log -1`
  echo "<a href=$branch_name>$branch_name</a><br>" >> $TMP_DIR/branches/index.html
}

create_apache_config_for_branch() {
  local branch_name="$1"
  test -z $branch_name && error "please use arguments when calling create_apache_config_for_branch"
  cat $MASTER_APACHE_CONFIG \
    | sed "s|^WSGIScriptAlias.*|WSGIScriptAlias /branches/$branch_name $BRANCH_DIR/$branch_name/adagios/wsgi.py process-group=adagios_$branch_name application-group=%{GLOBAL}|" \
    | sed "s|^Alias.*|Alias /branches/$branch_name/media $BRANCH_DIR/$branch_name/adagios/media|" \
    | sed "s|^WSGIDaemonProcess.*|WSGIDaemonProcess adagios_$branch_name user=nagios group=nagios processes=1 threads=25 python-path=$BRANCH_DIR/$branch_name|" \
    | sed "s|^WSGIProcessGroup adagios.*|WSGIProcessGroup adagios_$branch_name|" \
    | sed "s|Location /adagios|Location /adagios_$branch_name|" \
    | sed "s|WSGIProcessGroup adagios|WSGIProcessGroup adagios_$branch_name|" \
    > $APACHE_CONFDIR/$branch_name.conf
    echo "WSGIPythonPath  $BRANCH_DIR/$branch_name" >> $APACHE_CONFDIR/$branch_name.conf
    #| sed "s|^.*||" \
}
create_branches() {
  set -e 
  test -d $LOCAL_REPO || git clone --recursive $GITHUB_REPO $LOCAL_REPO
  cd $LOCAL_REPO
  #git pull --all
  for remote in `git branch -r | grep -v origin/HEAD`; do
    git branch --track $remote > /dev/null 2&>1 || echo ok > /dev/null
  done
  for remote in `git branch -r | grep -v origin/HEAD`; do
    cd $LOCAL_REPO
    branch_name=`echo $remote | sed 's|origin/||'`
    test -z $branch_name && continue
    git checkout $branch_name > /dev/null
    git clone -b $branch_name $LOCAL_REPO $TMP_DIR/branches/$branch_name > /dev/null 
    create_apache_config_for_branch $branch_name
    add_link_to_index_page $branch_name
    

  done
}

clean_branch_dir() {
  set -e
  cd $BRANCH_DIR && find . -type d -exec rm -rf {} \n
}

copy_from_working_path_to_production() {
  set -e
  mv $BRANCH_DIR $TMP_DIR/branches.old
  mv $TMP_DIR/branches $BRANCH_DIR
}
clean_apache_configuration;
create_branches;
copy_from_working_path_to_production;
service httpd reload

