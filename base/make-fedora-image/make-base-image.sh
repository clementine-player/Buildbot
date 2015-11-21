set -xe

version=$1

root=/data/fedora-$version-i386

rm -rf $root
mkdir $root

rpm --root $root --initdb
yumdownloader --releasever $version --destdir=/tmp fedora-release fedora-repos
rpm --nodeps --root $root -ivh /tmp/fedora-*.rpm
yum -y --nogpgcheck --installroot $root install yum
yum -y --nogpgcheck --installroot $root groupinstall "minimal install"
