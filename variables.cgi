#!/usr/bin/perl

$|++;
#use CGI::Carp qw(fatalsToBrowser);
use strict;
use XML::Simple;
use XML::Parser::Lite::Tree;
use CGI;

	my $cgi = new CGI;
	my $call = 'n8qq';

	# get xml
	my $xml_url = "http://xml.n8qq.com/aprs/1.2/report.cgi?call=$call";
	my $xml_content = get_url($xml_url);
	chomp $xml_content;
	$xml_content =~ s/(\r|\n)//g;
#	my $xml = XMLin(
#		$xml_content,
#		SuppressEmpty => 0
#	);
#	if (!$xml->{position})
#	{
#		print $cgi->header;
#		print "Error: The callsign \"$call\" was not found in aprsworld.net.\n";
#		exit;
#	}

	$xml_content =~ s/<\?.*?>//g;

	my $prev_node;
	my (@stack,@print);
	while ($xml_content =~ s/<(.*?)>//)
	{
		my $node = $1;
		if ($node =~ s/^\///)
		{
			push(@print,join(' ',@stack)) if $prev_node eq $node;
			pop @stack;
		} else {
			push @stack,$node;
		}
		$prev_node = $node;
	}
	print $cgi->header('text/plain');
	print "Copy and paste any of the following variables into your HTML page...\n\n";
	foreach my $line (@print)
	{
		$line =~ s/^station //;
		print "aprs($line)\n";
	}
	print "\n" x 20;


sub get_url
{
	my $url = shift;
	require LWP::UserAgent;
	my $ua = LWP::UserAgent->new( timeout=>10 );
	my $request = HTTP::Request->new('GET', $url);
	my $response = $ua->request($request);
	if (!$response->is_success)
	{
		print $cgi->header;
		print "Could not retrieve $url:<br /> ";
		print HTTP::Status::status_message($response->code);
		exit;
	}
	return $response->content;
}

