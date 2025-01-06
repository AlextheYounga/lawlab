commit_msg=$1
description=$2

source .env
cd USC_REPO

git add .
git commit -F- <<EOF
$commit_msg

$description
EOF

cd -