# timeconvert

In forensic investigations, timestamps often play a very important role in finding out what happened when. Unfortunately, there are several timestamp formats and automatically converting between them can be a hassle.

This Python script allows you to convert various formats of timestamps to Python datetime.datetime objects and back. It also provides for timezone conversion.

Read the TIMESTAMP_INFO variable for information about the available timestamp formats and their precision. Note that some timestamp formats are actually more precise; unfortunately, datetime objects only allow for microsecond resolution.

Currently supported timestamp formats are:
* UNIX timestamp
* UNIX timestamp with decimals
* JavaScript timestamp
* PRTime
* Webkit format
* Mac Absolute Time
* Windows FILETIME
* Windows SYSTEMTIME
* DOS/FAT time
* OLE Automation Date

Interface:
* convert_to_datetime(time_type, timestamp) takes a timestamp format and a timestamp, and returns a datetime. The datetime is a UTC datetime, except for conversions from DOS/FAT time, where the timestamp is always in local time without timezone information.
* convert_to_timestamp(time_type, datetime) does the opposite. 
* convert_to_timezone(datetime, timezone) takes a UTC datetime as returned by convert_to_datetime and transforms it into the Olson timezone (Europe/Berlin, Pacific/Auckland, ...) given in the second argument as string.

Contact us at info@digifors.de if you found an error or if you would like to see further timestamp formats added.

## License

MIT
