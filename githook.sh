source .env
cd USC_REPO

git add .
git commit -F- <<EOF
autocommit: update usc $(date +"%Y-%m-%d")

Automated commit to sync USC repo with the latest data.
$(date)
EOF

cd -