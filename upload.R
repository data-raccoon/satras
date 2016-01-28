library(googlesheets)
library(magrittr)
library(data.table)

path_in <- "brawl_trueskill.csv"
data_brawl <- fread(path_in)
sheetname = "Sheet2"

gs <- gs_url("https://docs.google.com/spreadsheets/d/143lcf3bei1cINsREiDTBQl9xjrZubVRBMRJvraybLr0/edit#gid=0")

wsheets <- gs_ws_ls(gs)
if (sheetname %in% wsheets){
    gs <- gs_ws_delete(gs, sheetname)
}
gs <- gs_ws_new(gs, sheetname)
gs_edit_cells(gs, ws = sheetname, input = data_brawl)

