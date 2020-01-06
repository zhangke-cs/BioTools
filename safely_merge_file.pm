#!/usr/bin/env perl

package safely_merge_file;
require Exporter;
require recursive_find_file;

use strict;
use warnings;
use IO::File;

our @ISA = qw(Exporter);
our @EXPORT = qw(safely_merge_file gzip_support);

=info
    Auther: Ke Zhang
    Date: 2020.01.05
=cut

=why
    safely_merge_file: I am receiving file format errors when running multiple tasks on HPC. I'm not sure what caused this error, but I implemented the following linux commands with perl to ensure the safety of the program.
    gzip_support: Generally, sequencing data is in gzip format. I wrote a piece of code for the file handle creation process for gzip format files.
=cut

=function
    safely_merge_file: safely_merge_file([folder],[output_file],[regex_of_input_file])
    return 0
    gzip_support: gzip_support([file_name],[input|output|append],[threads_number])
    return a string used for file handle creation
=cut

=license
Copyright 2020 zhangke-cs

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
=cut

sub safely_merge_file {
    #Function: safely merge file
    #require: recursive_find_file
    #require: gzip_support
    my $dir = shift;
    my $output_file = shift;
    my $regex_filter_strings = shift;
    my $all_file = recursive_find_file($dir);
    my @all_file = @{$all_file};
    my @regex_file = grep { $_ =~ /$regex_filter_strings/ } @all_file;
    #open output handle
    my $output_gzip_strings = gzip_support($output_file,'append',4);
    my $output_handle = new IO::File "$output_gzip_strings" or die "$!";
    foreach my $every_file (@regex_file){
        my $input_handle = new IO::File "$every_file" or die "$!";
        while (<$input_handle>) {
            print $output_handle $_;
        }
        $input_handle -> close;
    }
    $output_handle -> close;
    return 0;
}

sub gzip_support {
    my $file = shift; #file address
    my $type = shift; #input or output or append output
    my $max_threads = shift;
    if ($file =~ /gz$/ or $file =~ /gzip$/){
        my $use_command = '';
        if (which('pigz')){
            $use_command = 'pigz';
        }elsif (which('gzip')){
            $use_command = 'gzip';
        }else{
            echo_error("gzip_support","gzip and pigz not found!");
        }
        #max_threads
        if ($use_command eq 'pigz' and defined $max_threads){
            $use_command .= ' -p '.$max_threads;
        }
        my $key_strings = '';
        switch ($type) {
            case 'output' { $key_strings = "| $use_command > $file"; }
            case 'append' { $key_strings = "| $use_command >> $file"; }
            case 'input' { $key_strings = "$use_command -dc $file |"; }
            else { echo_error("gzip_support","unknown type: $type !"); }
        }
        return $key_strings;
    }else{
        my $key_strings = '';
        switch ($type) {
            case 'output' { $key_strings = "> $file"; }
            case 'append' { $key_strings = ">> $file"; }
            case 'input' { $key_strings = "$file"; }
            else { echo_error("gzip_support","unknown type: $type !"); }
        }
        return $key_strings;
    }
}
