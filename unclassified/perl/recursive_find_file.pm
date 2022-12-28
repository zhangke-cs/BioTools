#!/usr/bin/env perl

package recursive_find_file;
require Exorter;

use strict;
use warnings;
use IO::File;
use Cwd qw(abs_path);

our @ISA = qw(Exporter);
our @EXPORT = qw(recursive_find_file);

=info
    Auther: Ke Zhang
    Date: 2020.01.05
=cut

=why
    Recently, I searched online for questions about how perl found all files in a folder, and got two results:
    1. File :: Find. Won't traverse
    2. opendir cooperates with the sub-function loop. Can't return results, not elegant, not perfect
    Neither of these meets my needs, so I implemented an algorithm that returns results using perl code
=cut

=function
    recursive_find_file([folder_path])
    return array address
=cut

=license
###MIT LICENSE###
Copyright 2020 zhangke-cs

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
=cut

sub recursive_find_file {
    my $find_path = shift;
    #if "find_path" is file then return it
    die "ERROR: recursive_find_file\n$find_path not found\n" if ! -e $find_path;
    return $find_path if -f $find_path;
    #open dir
    opendir DIR,"$find_path" or die "$!";
    my @file = readdir DIR;
    closedir DIR;
    #cycles
    my @all_file;
    for my $every_file (@file) {
        next if $every_file =~ /^\./;
        #abs_path
        my $file_path = abs_path($find_path.'/'.$every_file);
        if (-f $file_path){
            push @all_file,$file_path;
        }else{
            #cycle this folder
            my @cycle_all_folder = ();
            push @cycle_all_folder,$file_path;
            while (1){
                #if shift return blank then jump out of the loop
                my $now_cycle_folder = shift @cycle_all_folder or last;
                #open dir
                opendir DIR,"$now_cycle_folder" or die "$!";
                my @cycle_read_file = readdir DIR;
                #filter . ..
                @cycle_read_file = grep { $_ !~ /^\./ } @cycle_read_file;
                #abs_path
                @cycle_read_file = map { abs_path($file_path.'/'.$_) } @cycle_read_file;
                #split file type
                my @cycle_file = grep { -f $_ } @cycle_read_file;
                my @cycle_folder = grep { -d $_ } @cycle_read_file;
                if (scalar @cycle_folder == 0){
                    push @all_file,@cycle_file if scalar @cycle_file != 0;
                    last;
                }else{
                    push @all_file,@cycle_file if scalar @cycle_file != 0;
                    push @cycle_all_folder,@cycle_folder;
                }
            }
        }
    }
    return \@all_file;
}
