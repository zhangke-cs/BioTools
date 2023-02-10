# File Line Split

## File Split
**file_split**中的'FileSlicer', 'MultiFileSlicer'类可以将普通文件按照行分割为多个大小近似的块。

## Fastq Split
**fastq_split**中的'FastqSlicer', 'MultiFastqSlicer'类可以将Fastq文件（单行序列和质量值）按照序列分割为多个大小近似的块。

## Scheme

用户输入的split_num（每个块大致的行数）或者chunk_size（每个块大致的大小），程序利用seek和tell方法找到文件中大致的位置，然后使用readline方法确定行末。

## Return

返回二维数组，每个元素是长度为3的Tuple，内容是“文件地址”，“开始位置”和“结束位置”。