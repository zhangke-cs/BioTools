#!/usr/bin/env perl

package read_complex_fasta;
require Exorter;

use strict;
use warnings;

our @ISA = qw(Exporter);
our @EXPORT = qw(read_complex_fasta);

=info
    Auther: Ke Zhang
    Date: 2020.04.30
=cut

=why
    As we all know, Bioperl is annoying, especially since I only want to read multiFASTA format files.
    In other words, in order to read the multiFASTA format, you do not need to use Bioperl in your project.
=cut

=function
    read_complex_fasta(a innput handle)
    return ($id, $decs, $seq)
=cut

=license
###MIT LICENSE###
Copyright 2020 zhangke-cs

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
=cut

=example
    my $input_handle = new IO::File "FASTAFILE" or die "$!";
    while (my ($id, $decs, $seq) = read_complex_fasta($input_handle)){
        #do somethings
        last if eof($input_handle); #Is the handle over?
    }
    close $input_handle;
=cut

our $read_fast_register = '#orgin#';
sub read_complex_fasta {
    my $input_handle = shift;
    my ($id,$decs);
    my $seq = '';
    if ($read_fast_register ne '#orgin#'){
        ($id, $decs) = _thread_fast_head($read_fast_register);
    }else{
        my $oneline = <$input_handle>;
        chomp $oneline;
        ($id, $decs) = _thread_fast_head($oneline);
    }
    while (my $line = <$input_handle>){
        chomp $line;
        $read_fast_register = $line and last if $line =~ /^[>@]/;
        $seq .= $line;
    }
    return $id,$decs,$seq;
}

sub _thread_fast_head {
    my $head_strings = shift;
    if ($head_strings =~ /^[>@](\S+?)\s(.*)$/){
        return $1,$2;
    }elsif ($head_strings =~ /^[>@](\S+?)$/){
        return $1,'none';
    }else{
        return 'none','none';
    }
}
