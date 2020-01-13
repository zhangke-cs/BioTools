#!/usr/bin/env perl
use strict;
use warnings;
use IO::File;
use POSIX qw(strftime);
use List::Util qw(sum);

#=function
#    Chinese
#    将这个脚本放在后台可以记录一段时间的CPU使用率和MEM使用率
#=cut
#
#=cpu_monitor
#    Chinese
#    CPU计算间隔是1秒钟
#=cut

while (1){
    my $cpu_strings = get_cpu_usage();
    my @mem_strings = get_mem_info();
    my $output_strings = 'CPU:'.$cpu_strings."\tMem:".$mem_strings[1].' '.$mem_strings[0];
    my $local_time = strftime "%Y%m%d-%H:%M:%S", localtime;
    print "[$local_time]: <Info> $output_strings\n";
}

sub get_cpu_usage {
    my $stat_one_line = `head -n1 /proc/stat` or die "$!";
    my @stat_one_line = $stat_one_line =~ /(\d+)/g;
    my $total_cpu_time = sum(@stat_one_line);
    sleep 1;
    my $stat_two_line = `head -n1 /proc/stat` or die "$!";
    my @stat_two_line = $stat_two_line =~ /(\d+)/g;
    my $total_cpu_time_2 = sum(@stat_two_line);
    my $total_idle = $stat_two_line[3] - $stat_one_line[3];
    my $total_usage = $total_cpu_time_2 - $total_cpu_time;
    my $total = (($total_usage - $total_idle) / $total_usage ) * 100;
    return $total;
}

sub get_mem_info {
    #MemTotal = MemFree +[Slab+ VmallocUsed + PageTables + KernelStack + HardwareCorrupted + Bounce + X]+[Cached + AnonPages + Buffers + (HugePages_Total * Hugepagesize)])
    my $meminfo_file = '/proc/meminfo';
    if ( -e $meminfo_file ){
        my $available_mem_size = 0; #units is GB
        my $available_mem_units = '';
        my $handle_meminfo = new IO::File "$meminfo_file" or die "$!";
        local $/ = undef;
        my $meminfo = <$handle_meminfo>;
        if ($meminfo =~ /MemAvailable:\s+(\d+)\s+(\w+)/){
            my $available_mem_value = $1;
            $available_mem_units = $2;
            if ($available_mem_units =~ /kb/i) {
                $available_mem_size = $available_mem_value;
            }elsif ($available_mem_units =~ /mb/i) {
                $available_mem_size = $available_mem_value * 1024;
            }elsif ($available_mem_units =~ /gb/i) {
                $available_mem_size = $available_mem_value * 1024 * 1024;
            }else{
                return "-2";
            }
            $handle_meminfo -> close;
            return $available_mem_units,$available_mem_size;
        }else{
            my $available_mem_size = 0;
            my $MemFree = 0;
            my $Buffer = 0;
            my $Cached = 0;
            my $units = '';
            if ($meminfo =~ /MemFree:\s+(\d+)\s+(\w+)/){
                $MemFree = $1;
                $units = $2;
            }
            if ($meminfo =~ /Buffer:\s+(\d+)\s+\w+/){
                $Buffer = $1;
            }
            if ($meminfo =~ /Cached:\s+(\d+)\s+\w+/){
                $Cached = $1;
            }
            my $available_mem_value = $MemFree + $Buffer + $Cached;
            if  ($units =~ /kb/i) {
                $available_mem_size = $available_mem_value;
            }elsif ($units =~ /mb/i) {
                $available_mem_size = $available_mem_value * 1024;
            }elsif ($units =~ /gb/i) {
                $available_mem_size = $available_mem_value * 1024 * 1024;
            }else{
                return -2;
            }
            $handle_meminfo -> close;
            return $units,$available_mem_size;
        }
    }else{
        return -1;
    }
}
