#!/bin/bash

time=$(date +"%Y_%m_%d_%I_%M_%p")

if [ ! -d reports ]; then
	mkdir reports
fi

for sql in sql/*.sql; do
	stem=$(basename $sql .sql)
	outfile="$stem-$time.csv"
	sqlite3 -header -csv ivirpt.sqlite3 < $sql > reports/$outfile
done
