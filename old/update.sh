#!/bin/bash
Rscript download.R
~/.virtualenvs/all/bin/python calc_trueskill.py
Rscript upload.R
