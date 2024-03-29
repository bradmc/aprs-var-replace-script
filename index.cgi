#!/usr/bin/perl

$|++;
use CGI::Carp qw(fatalsToBrowser);
use strict;
use XML::Simple;
use CGI;

	my $function_prefix = 'aprs'; # for backward compatability with the aprs() functions
	my $var_prefix = '\$';
	my $xml_timeout = 60; # seconds to timeout for the call to the xml script
	my $page_timeout = 30; # seconds to timeout for the call to the remote page

	my $cgi = new CGI;
	my $call;
	my $url;
	if ($ENV{PATH_INFO})
	{
		(my $junk,$call,$url) = split '/',$ENV{PATH_INFO},3;
	} else {
		$call = $cgi->param('call');
		$url = $cgi->param('url');
	}		

	$url = 'http://'.$url if $url !~ /\:\/\//;

	# if this is just a request for the list of variables
	if ($cgi->param('varlist'))
	{
		print $cgi->header;
		list_variables($cgi->param('sort'));
		exit;
	}

	# get xml
	my $xml_url = "http://www.aprsearch.net/aprs/1.3/report.cgi?call=$call";
	my $xml_content = get_url($xml_url,$xml_timeout);
	chomp $xml_content;
	$xml_content =~ s/(\r|\n)//g;
	my $xml = XMLin(
		$xml_content,
		SuppressEmpty => 0
	);
	if (!$xml->{position})
	{
		print $cgi->header;
		print "Error: The callsign \"$call\" was not found in aprsworld.net.\n";
		exit;
	}

	# get web page
	my $content = get_url($url,$page_timeout);

	# replace variables
	if ($content =~ /aprs\(.*?\)/)
	{
		# for backward compatability with the aprs() functions
		$content =~ s/$function_prefix\((.*?)\)/filter_aprs($1)/egi;
	} else {
		my $vars = set_vars($xml);
		$content = replace_vars($content,$vars);
	}
	print $cgi->header;
	print $content;



# -------------------------------------------------------------------------------------
#	ROUTINES
# -------------------------------------------------------------------------------------

sub list_variables
{
	my $sort = shift || 'related';
	my $vars = set_vars();
	print qq{
		<html><head><title>List of Variables</title>
		<style type="text/css"><!-- a { text-decoration: none; color: #0000a0; } body, td, p, dd { font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 11px; line-height: 15px;} --></style></head>
		<body><center>
	};
	print qq{[<a href="./index.cgi?varlist=1&sort=};
	print $sort eq 'related' ? 'alpha">Sort Variables Alphabetically' : 'related">Sort Related Variables Together';
	print "</a>] &nbsp;&nbsp;&nbsp;";
	print qq{[<a href="./">Return to Documentation Page</a>]};
	print "\n<p />\n";
	print qq{
		<table cellspacing="0" cellpadding="4" border="1">
		<tr bgcolor="#f0f0f0" align="center"><td><strong>Variable</strong></td><td><strong>Description</strong></td></tr>
	};
	my @sorted_vars;
	if ($sort eq 'related')
	{
		@sorted_vars = sort {$vars->{$a}->{sort} <=> $vars->{$b}->{sort}} keys %$vars;
	} else {
		@sorted_vars = sort keys %$vars;
	}

	foreach (@sorted_vars)
	{
		$var_prefix =~ s/\\//g;
		print "<tr><td nowrap>$var_prefix$_</td><td>$vars->{$_}->{desc}</td></tr>\n";
	}
	print "</table>\n";
	print '<br />' x 10;
	print qq{
		</center></body></html>
	};
}

sub replace_vars
{
	my $content = shift;
	my $vars = shift;
	foreach (keys %$vars)
	{
		# $content =~ s/$var_prefix$_\b/$vars->{$_}->{value}/gi;
		$content =~ s/$var_prefix$_\b/$vars->{$_}->{value}/gi;
	}
	return $content;
}

sub filter_aprs
{
	my $arg = shift;
	my @arg = split /\s+/,$arg;
	my $xml_eval = "\$xml";
	foreach (@arg) { $xml_eval .= "->{$_}" }
	my $value = eval $xml_eval;
	$value = "Error: \"$function_prefix($arg)\" is not a complete variable reference." if $value =~ /^HASH\(/;
	# $value = "Error: \"$function_prefix($arg)\" is not a valid variable reference." if (eval "! exists $xml_eval");
	return $value;
}

sub get_url
{
	my $url = shift;
	my $timeout = shift;
	require LWP::UserAgent;
	my $ua = LWP::UserAgent->new( timeout=>$timeout );
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

sub set_vars
{
	my $xml = shift;
	my $vars = {
		'call' => {
			value => $xml->{callsign},
			desc  => 'Station callsign.',
			sort  => 10,
		},
		'lat_min' => {
			value => $xml->{position}->{latitude}->{degrees_minutes},
			desc  => 'Latitude of station in degrees and minutes.',
			sort  => 40,
		},
		'lon_min' => {
			value => $xml->{position}->{longitude}->{degrees_minutes},
			desc  => 'Longitude of station in degrees and minutes.',
			sort  => 50,
		},
		'lat' => {
			value => $xml->{position}->{latitude}->{degrees},
			desc  => 'Latitude of station in degrees.',
			sort  => 20,
		},
		'lon' => {
			value => $xml->{position}->{longitude}->{degrees},
			desc  => 'Longitude of station in degrees.',
			sort  => 30,
		},
		'symbol_overlay' => {
			value => $xml->{symbol_table},
			desc  => 'Symbol overlay.',
			sort  => 60,
		},
		'symbol' => {
			value => $xml->{symbol_code},
			desc  => 'Symbol.',
			sort  => 70,
		},
		'speed' => {
			value => $xml->{position}->{speed}->{mph},
			desc  => 'Speed of the station in MPH.',
			sort  => 80,
		},
		'speed_kph' => {
			value => $xml->{position}->{speed}->{kph},
			desc  => 'Speed of the station in KPH.',
			sort  => 90,
		},
		'speed_knots' => {
			value => $xml->{position}->{speed}->{knots},
			desc  => 'Speed of the station in knots.',
			sort  => 100,
		},
		'dir_loc' => {
			value => $xml->{position}->{nearest}->{direction},
			desc  => 'Direction from the nearest location.',
			sort  => 230,
		},
		'dir_deg' => {
			value => $xml->{position}->{course}->{degrees},
			desc  => 'Direction of the station in degrees.',
			sort  => 120,
		},
		'dir' => {
			value => $xml->{position}->{course}->{direction},
			desc  => 'Direction of the station as a string.  (Example: NNW)',
			sort  => 110,
		},
		'alt_m' => {
			value => $xml->{position}->{altitude}->{meters},
			desc  => 'Altitude of the station in meters.',
			sort  => 140,
		},
		'alt' => {
			value => $xml->{position}->{altitude}->{feet},
			desc  => 'Altitude of the station in feet.',
			sort  => 130,
		},
		'street_map' => {
			value => $xml->{position}->{maps}->{street},
			desc  => 'URL to station plotted on a street level map.',
			sort  => 150,
		},
		'city_map' => {
			value => $xml->{position}->{maps}->{town},
			desc  => 'URL to station plotted on a city/town level map.',
			sort  => 160,
		},
		'county_map' => {
			value => $xml->{position}->{maps}->{county},
			desc  => 'URL to station plotted on a county level map.',
			sort  => 170,
		},
		'regional_map' => {
			value => $xml->{position}->{maps}->{regional},
			desc  => 'URL to station plotted on a regional level map.',
			sort  => 180,
		},
		'loc' => {
			value => $xml->{position}->{nearest}->{name},
			desc  => 'Nearest location.',
			sort  => 190,
		},
		'state' => {
			value => $xml->{position}->{nearest}->{state},
			desc  => 'State of the nearest location.',
			sort  => 200,
		},
		'country' => {
			value => $xml->{position}->{nearest}->{country},
			desc  => 'Country of the nearest location.',
			sort  => 210,
		},
		'dist' => {
			value => $xml->{position}->{nearest}->{distance},
			desc  => 'Distance from the nearest location, in miles.',
			sort  => 220,
		},
		'age_days' => {
			value => $xml->{position}->{age}->{days},
			desc  => 'Number of days since this packet was received.',
			sort  => 240,
		},
		'age_days_pad' => {
			value => sprintf("%.2d", $xml->{position}->{age}->{days}),
			desc  => 'Number of days since this packet was received, padded to two digits.',
			sort  => 241,
		},
		'age_hours' => {
			value => $xml->{position}->{age}->{hours},
			desc  => 'Number of hours since this packet was received.',
			sort  => 250,
		},
		'age_hours_pad' => {
			value => sprintf("%.2d", $xml->{position}->{age}->{hours}),
			desc  => 'Number of hours since this packet was received, padded to two digits.',
			sort  => 251,
		},
		'age_min' => {
			value => $xml->{position}->{age}->{minutes},
			desc  => 'Number of minutes since this packet was received.',
			sort  => 260,
		},
		'age_min_pad' => {
			value => sprintf("%.2d", $xml->{position}->{age}->{minutes}),
			desc  => 'Number of minutes since this packet was received, padded to two digits.',
			sort  => 261,
		},
		'age_sec' => {
			value => $xml->{position}->{age}->{seconds},
			desc  => 'Number of seconds since this packet was received.',
			sort  => 270,
		},
		'age_sec_pad' => {
			value => sprintf("%.2d", $xml->{position}->{age}->{seconds}),
			desc  => 'Number of seconds since this packet was received, padded to two digits.',
			sort  => 271,
		},
		'month' => {
			value => $xml->{position}->{date}->{month},
			desc  => 'Month the packet was received.  (UTC)',
			sort  => 280,
		},
		'day' => {
			value => $xml->{position}->{date}->{day},
			desc  => 'Day the packet was received.  (UTC)',
			sort  => 290,
		},
		'year' => {
			value => $xml->{position}->{date}->{year},
			desc  => 'Year the packet was received.  (UTC)',
			sort  => 300,
		},
		'hour' => {
			value => $xml->{position}->{time}->{hour},
			desc  => 'Hour the packet was received.  (UTC)',
			sort  => 310,
		},
		'min' => {
			value => sprintf("%.2d", $xml->{position}->{time}->{minute}),
			desc  => 'Minute the packet was received.  (with leading padded zero)',
			sort  => 320,
		},
		'sec' => {
			value => sprintf("%.2d", $xml->{position}->{time}->{second}),
			desc  => 'Second the packet was received.  (with leading padded zero)',
			sort  => 330,
		},
		'temp_f' => {
			value => $xml->{weather}->{temperature}->{fahrenheit},
			desc  => 'Temperature at weather station, in Fahrenheit.',
			sort  => 340,
		},
		'temp_c' => {
			value => $xml->{weather}->{temperature}->{celsius},
			desc  => 'Temperature at weather station, in Celsius.',
			sort  => 350,
		},
		'dewpoint_f' => {
			value => $xml->{weather}->{dewpoint}->{fahrenheit},
			desc  => 'Dewpoint at weather station, in Fahrenheit.',
			sort  => 355,
		},
		'dewpoint_c' => {
			value => $xml->{weather}->{dewpoint}->{celsius},
			desc  => 'Dewpoint at weather station, in Celsius.',
			sort  => 356,
		},
		'humidity' => {
			value => $xml->{weather}->{humidity},
			desc  => 'Humidity at weather station.',
			sort  => 360,
		},
		'bar_hpa' => {
			value => $xml->{weather}->{barometer}->{hpa},
			desc  => 'Barometric pressure at weather station, in hPa.',
			sort  => 370,
		},
		'bar_mmhg' => {
			value => $xml->{weather}->{barometer}->{mmhg},
			desc  => 'Barometric pressure at weather station, in mmHg.',
			sort  => 380,
		},
		'bar_inhg' => {
			value => $xml->{weather}->{barometer}->{inhg},
			desc  => 'Barometric pressure at weather station, in inHg.',
			sort  => 390,
		},
		'luminosity' => {
			value => $xml->{weather}->{luminosity},
			desc  => 'Luminosity at weather station.',
			sort  => 400,
		},
		'wind_speed_kph' => {
			value => $xml->{weather}->{wind}->{speed}->{kph},
			desc  => 'Wind speed at weather station in KPH.',
			sort  => 420,
		},
		'wind_speed' => {
			value => $xml->{weather}->{wind}->{speed}->{mph},
			desc  => 'Wind speed at weather station in MPH.',
			sort  => 410,
		},
		'wind_speed_knots' => {
			value => $xml->{weather}->{wind}->{speed}->{knots},
			desc  => 'Wind speed at weather station in knots.',
			sort  => 430,
		},
		'wind_dir' => {
			value => $xml->{weather}->{wind}->{direction}->{direction},
			desc  => 'Wind direction at weather station.',
			sort  => 440,
		},
		'wind_dir_deg' => {
			value => $xml->{weather}->{wind}->{direction}->{degrees},
			desc  => 'Wind direction at weather station in degrees.',
			sort  => 450,
		},
		'wind_gust' => {
			value => $xml->{weather}->{wind}->{gust}->{mph},
			desc  => 'Wind gust at weather station in MPH.',
			sort  => 460,
		},
		'wind_gust_kph' => {
			value => $xml->{weather}->{wind}->{gust}->{kph},
			desc  => 'Wind gust at weather station in KPH.',
			sort  => 470,
		},
		'wind_gust_knots' => {
			value => $xml->{weather}->{wind}->{gust}->{knots},
			desc  => 'Wind gust at weather station in knots.',
			sort  => 480,
		},
		'wind_sus_kph' => {
			value => $xml->{weather}->{wind}->{sus}->{kph},
			desc  => 'Sustained wind at weather station in KPH.',
			sort  => 500,
		},
		'wind_sus_knots' => {
			value => $xml->{weather}->{wind}->{sus}->{knots},
			desc  => 'Sustained wind at weather station in knots.',
			sort  => 510,
		},
		'wind_sus' => {
			value => $xml->{weather}->{wind}->{sus}->{mph},
			desc  => 'Sustained wind at weather station in MPH.',
			sort  => 490,
		},
		'rain_hour' => {
			value => $xml->{weather}->{rain}->{hour}->{in},
			desc  => 'Rain over the last hour, in inches.',
			sort  => 520,
		},
		'rain_hour_cm' => {
			value => $xml->{weather}->{rain}->{hour}->{cm},
			desc  => 'Rain over the last hour, in centimeters.',
			sort  => 530,
		},
		'rain_today' => {
			value => $xml->{weather}->{rain}->{day_calendar}->{in},
			desc  => 'Rain during the current calendar day, in inches.',
			sort  => 540,
		},
		'rain_today_cm' => {
			value => $xml->{weather}->{rain}->{day_calendar}->{cm},
			desc  => 'Rain during the current calendar day, in centimeters.',
			sort  => 550,
		},
		'rain_24hr' => {
			value => $xml->{weather}->{rain}->{day_24hour}->{in},
			desc  => 'Rain over the last 24 hours, in inches.',
			sort  => 560,
		},
		'rain_24hr_cm' => {
			value => $xml->{weather}->{rain}->{day_24hour}->{cm},
			desc  => 'Rain over the last 24 hours, in centimeters.',
			sort  => 570,
		},
		'comment' => {
			value => $xml->{status}->{comment},
			desc  => 'Station comment.',
			sort  => 580,
		},
		'power' => {
			value => $xml->{status}->{power},
			desc  => 'Transmit power in watts.',
			sort  => 590,
		},
		'ant_ht' => {
			value => $xml->{status}->{height},
			desc  => 'Antenna height in feet.',
			sort  => 600,
		},
		'ant_gain' => {
			value => $xml->{status}->{gain},
			desc  => 'Antenna gain in dB.',
			sort  => 610,
		},
		'ant_dir' => {
			value => $xml->{status}->{directivity},
			desc  => 'Antenna directivity.',
			sort  => 620,
		},
		'rate' => {
			value => $xml->{status}->{rate},
			desc  => 'Rate.',
			sort  => 630,
		},
#		'' => {
#			value => $xml->{}->{}->{}->{},
#			desc  => '',
#			sort  => ,
#		}
	};
	return $vars;
}



