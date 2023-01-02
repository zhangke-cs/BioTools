#!/usr/bin/env Rscript

#0 get parameters
library(optparse)
option_list <- list(
    make_option(c("-o", "--otu_file"), type = "character", help="TSV, otu_table.txt"),
    make_option(c("-g", "--group_file"), type = "character", help="TSV, group.txt"),
    make_option(c("-t", "--taxonomy_file"), type = "double", help="TSV, taxonomy.txt"),
    make_option(c("-p", "--plot_output"), type = "character", help="how to sort drug by effi scores."),
    make_option(c("--plot_type"), type = "character", help="maximum herb_score threshold")
)
opt <- parse_args(OptionParser(option_list=option_list))

#1 check parameters
check_vector <- c('otu_file', 'group_file', 'taxonomy_file')
for (every_opt in check_vector){
 if ( ! every_opt %in% names(opt)){
  message("Plase, usage Rscript reduce_achieve.r -h|--help !")
  stop(sprintf("Required parameters are missing: %s", every_opt))
 }
}

if (file.access(opt$otu_file) == -1){
    stop(sprintf("File not found: %s", opt$otu_file))
}
if (file.access(opt$group_file) == -1){
    stop(sprintf("File not found: %s", opt$group_file))
}
if (file.access(opt$taxonomy_file) == -1){
    stop(sprintf("File not found: %s", opt$taxonomy_file))
}

#2 loading library
library(circlize)
library(reshape2)
library(ComplexHeatmap)
library(grid)

#3 setting colors
color_otu <- c('#8DD3C7', '#FFFFB3', '#BEBADA', '#FB8072', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5', '#BC80BD', '#CCEBC5', '#FFED6F', '#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF', '#66C2A5')
color_sample <- c('#6181BD', '#F34800', '#64A10E', '#FF00FF', '#c7475b', '#049a0b')
color_phylum <- c('#BEAED4', '#FDC086', '#FFFF99', '#386CB0', '#F0027F')
color_group <- c('#4253ff', '#ff4308')

#4 read data
#OTU_ID phylum        detail
#OTU_1  Proteobacteria p__Proteobacteria;c__Alphaproteobacteria;o__Sphingomonadales;f__Sphingomonadaceae 
taxonomy_info <- read.table(opt$taxonomy_file, sep = '\t', stringsAsFactors = F, header = T, row.names = 1)
#tax_phylum <- unique(taxonomy$phylum)
#taxonomy$phylum <- factor(taxonomy$phylum, levels = tax_phylum)
taxonomy_info$phylum <- as.factor(taxonomy_info$phylum)
#all_otu <- taxonomy$OTU_ID
#taxonomy$OTU_ID <- factor(taxonomy$OTU_ID, levels = all_otu)

#sample_ID group_ID
#N1        N
group_info <- read.table(opt$group_file, sep = '\t', stringsAsFactors = F, header = T)
group_info$group_ID <- as.factor(group_info$group_ID)

#all_group <- unique(group_info$group_ID)  #all_group 删除
#group_info$group_ID <- factor(group_info$group_ID, levels = all_group)

if (length(unique(group_info$sample_ID)) < length(group_info$sample_ID)){
    stop(sprintf("Sample ID is duplicate! Exit."))
}
#all_sample <- group_info$sample_ID

#OTU_ID N1  N2  N3  C1   C2   C3
#OTU_21 235 671 989 1904 1003 637
otu_table <- read.table(opt$otu_file, sep = '\t', stringsAsFactors = F, header = T, row.names = 1)
otu_taxonomy <- merge(taxonomy_info, otu_table, by = 'row.names')
otu_taxonomy <- otu_taxonomy[order(otu_taxonomy$phylum, otu_taxonomy$OTU_ID), ]
#rownames(otu_table) <- otu_table$OTU_ID
#otu_table <- otu_table[all_sample]

#5 
##生成绘图文件
#circlize 外圈属性数据
#all_ID <- c(all_otu, all_sample)
all_ID <- c(otu_taxonomy$Row.names, group_info$sample_ID)
#accum_otu <- rowSums(otu_table)
accum_otu <- rowSums(otu_taxonomy[group_info$sample_ID])
accum_sample <- colSums(otu_taxonomy[group_info$sample_ID])
all_ID_xlim <- cbind(rep(0, length(all_ID)),data.frame(c(accum_otu, accum_sample)))

#circlize 内圈连线数据
#otu_table$otu_ID <- all_otu
#plot_data <- melt(otu_table, id = 'otu_ID')
plot_data <- melt(otu_taxonomy[c('Row.names', group_info$sample_ID)], id = 'Row.names')
colnames(plot_data)[1:2] <- c('otu_ID', 'sample_ID')

plot_data$otu_ID <- factor(plot_data$otu_ID, levels = otu_taxonomy$Row.names)
plot_data$sample_ID <- factor(plot_data$sample_ID, levels = group_info$sample_ID)
plot_data <- plot_data[order(plot_data$otu_ID, plot_data$sample_ID), ]
plot_data <- plot_data[c(2, 1, 3, 3)]

#颜色设置
names(color_otu) <- otu_taxonomy$Row.names
names(color_sample) <- group_info$sample_ID

####circlize 绘图
#!!! 这里换用ggsave保存图像
pdf('circlize_plot.pdf', width = 20, height = 8)
circle_size = unit(1, 'snpc')

##整体布局
gap_size <- c(rep(3, length(all_otu) - 1), 6, rep(3, length(all_sample) - 1), 6)
circos.par(cell.padding = c(0, 0, 0, 0), start.degree = 270, gap.degree = gap_size)
circos.initialize(factors = factor(all_ID, levels = all_ID), xlim = all_ID_xlim)

##绘制 OTU 分类、样本分组区块（第一圈）
circos.trackPlotRegion(
 ylim = c(0, 1), track.height = 0.03, bg.border = NA, 
 panel.fun = function(x, y) {
  sector.index = get.cell.meta.data('sector.index')
  xlim = get.cell.meta.data('xlim')
  ylim = get.cell.meta.data('ylim')
 } )

for (i in 1:length(tax_phylum)) {
 tax_OTU <- {subset(taxonomy, phylum == tax_phylum[i])}$OTU_ID
 highlight.sector(tax_OTU, track.index = 1, col = color_phylum[i], text = tax_phylum[i], cex = 0.5, text.col = 'black', niceFacing = FALSE)
}

for (i in 1:length(all_group)) {
 group_sample <- {subset(group, group_ID == all_group[i])}$sample_ID
 highlight.sector(group_sample, track.index = 1, col = color_group[i], text = all_group[i], cex = 0.7, text.col = 'black', niceFacing = FALSE)
}

##各 OTU、样本绘制区
#添加百分比注释（第二圈）
circos.trackPlotRegion(
 ylim = c(0, 1), track.height = 0.05, bg.border = NA, 
 panel.fun = function(x, y) {
  sector.index = get.cell.meta.data('sector.index')
  xlim = get.cell.meta.data('xlim')
  ylim = get.cell.meta.data('ylim')
 } )

circos.track(
 track.index = 2, bg.border = NA, 
 panel.fun = function(x, y) {
  xlim = get.cell.meta.data('xlim')
  ylim = get.cell.meta.data('ylim')
  sector.name = get.cell.meta.data('sector.index')
  xplot = get.cell.meta.data('xplot')
  
  by = ifelse(abs(xplot[2] - xplot[1]) > 30, 0.25, 1)
  for (p in c(0, seq(by, 1, by = by))) circos.text(p*(xlim[2] - xlim[1]) + xlim[1], mean(ylim) + 0.4, paste0(p*100, '%'), cex = 0.4, adj = c(0.5, 0), niceFacing = FALSE)
  
  circos.lines(xlim, c(mean(ylim), mean(ylim)), lty = 3)
 } )

#绘制 OTU、样本主区块（第三圈）
circos.trackPlotRegion(
 ylim = c(0, 1), track.height = 0.03, bg.col = c(color_otu, color_sample), bg.border = NA, track.margin = c(0, 0.01),
 panel.fun = function(x, y) {
  xlim = get.cell.meta.data('xlim')
  sector.name = get.cell.meta.data('sector.index')
  circos.axis(h = 'top', labels.cex = 0.4, major.tick.percentage = 0.4, labels.niceFacing = FALSE)
  circos.text(mean(xlim), 0.2, sector.name, cex = 0.4, niceFacing = FALSE, adj = c(0.5, 0))
 } )

#绘制 OTU、样本副区块（第四圈）
circos.trackPlotRegion(ylim = c(0, 1), track.height = 0.03, track.margin = c(0, 0.01))

##绘制 OTU-样本关联连线（最内圈）
for (i in seq_len(nrow(plot_data))) {
 circos.link(
  plot_data[i,2], c(accum_otu[plot_data[i,2]], accum_otu[plot_data[i,2]] - plot_data[i,4]),
  plot_data[i,1], c(accum_sample[plot_data[i,1]], accum_sample[plot_data[i,1]] - plot_data[i,3]),
  col = paste0(color_otu[plot_data[i,2]], '70'), border = NA )
 
 circos.rect(accum_otu[plot_data[i,2]], 0, accum_otu[plot_data[i,2]] - plot_data[i,4], 1, sector.index = plot_data[i,2], col = color_sample[plot_data[i,1]], border = NA)
 circos.rect(accum_sample[plot_data[i,1]], 0, accum_sample[plot_data[i,1]] - plot_data[i,3], 1, sector.index = plot_data[i,1], col = color_otu[plot_data[i,2]], border = NA)
 
 accum_otu[plot_data[i,2]] = accum_otu[plot_data[i,2]] - plot_data[i,4]
 accum_sample[plot_data[i,1]] = accum_sample[plot_data[i,1]] - plot_data[i,3]
}

##添加图例
otu_legend <- Legend(
  at = all_otu, labels = taxonomy$detail, labels_gp = gpar(fontsize = 8),    
  grid_height = unit(0.5, 'cm'), grid_width = unit(0.5, 'cm'), type = 'points', pch = NA, background = color_otu)

pushViewport(viewport(x = 0.85, y = 0.5))
grid.draw(otu_legend)
upViewport()
  
##清除 circlize 样式并关闭画板
circos.clear()
dev.off()
