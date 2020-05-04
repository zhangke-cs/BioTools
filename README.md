# zhangke-cs's BioTools

Introduction
---------------------------
Stored here are frequently used programs in bioinformatics analysis.
Unless otherwise stated, all code here is open sourced under the **MIT License**

PERL Code
---------------------------
1. recursive_find_file.pm  
Function: Recursively list all files in a directory  
Return: A array reference  

2. safely_merge_file.pm  
Function: Merge files using PERL code  
Return: 0  
Function: Generate a string for file handle creation  
Return: A string  

3. read_complex_fasta.pm  
Function: Read multi line FASTA  
Return: $id, $desc, $seq  

4. monitor_cpu_and_mem.pl  
Function: Monitor CPU and MEM usage from Linux system files  
Return: A string  

5. anyexec.pl
Function: Execute PERL script like BASH script

PBS
---------------------------
1. mpi_run.pl
Function: At the node level, synchronize the --nodes parameter of mpirun with the resources allocated by PBS  

