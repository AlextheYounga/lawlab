source ./.env

commit_msg=$1
description=$2

cd $USC_REPO

git add .
git commit -F- <<EOF
$commit_msg

$description
EOF

cd -