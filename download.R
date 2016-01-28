library(googlesheets)
library(magrittr)

gs <- gs_url("https://docs.google.com/spreadsheets/d/143lcf3bei1cINsREiDTBQl9xjrZubVRBMRJvraybLr0/edit#gid=0")
path_out <- "brawl_ranks.csv"

data_brawl <- gs_read(gs, range = paste0("A2:F", as.character(gs$ws$row_extent[1])))
write.csv(data_brawl, path_out, row.names = FALSE)
