#!/usr/bin/env bash

# Remote Machine
sudo useradd git
sudo passwd git
su git
cd ~
mkdir Repository
cd Repository
mkdir -p ptolemy.git
cd ptolemy.git
git init --bare

# Local Machine
sudo apt-get install git-core
ssh keygen -t rsa
cat ~/.ssh/id_rsa.pub | ssh git@ptolemy.thewanderinggod.tech "mkdir -p ~/.ssh && cat >>  ~/.ssh/authorized_keys"
cd ~/Ptolemy
touch .gitignore
printf "include/zips/*\n__pycache__/*\ntechnical/*\n/temp/*" >> .gitignore
git init
git add .
git config --global user.email "the.wandering.god@gmail.com"
git config --global user.name "Michael Rendier"
git commit -m "First File Add" -a
git push origin master