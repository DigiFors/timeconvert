"""
Copyright (c) 2016 DigiFors GmbH, Leipzig

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from datetime import datetime, timedelta 
import pytz
import time
import struct

class TimeConverter:
  
  # The various formats supported.
  UNIX = 0
  UNIX_DECIMAL = 1
  JAVASCRIPT = 2
  PRTIME = 3
  WEBKIT_FORMAT = 4
  MAC_ABSOLUTE_TIME = 5
  FILETIME = 6
  SYSTEMTIME = 7
  DOS = 8
  OLE = 9
  
  TIMESTAMP_INFO = {UNIX: ("UNIX timestamp", timedelta(seconds=1)),
                    UNIX_DECIMAL: ("UNIX timestamp with decimals", timedelta(microseconds=1)),
                    JAVASCRIPT: ("JavaScript timestamp", timedelta(microseconds=1000)),
                    PRTIME: ("PRTime", timedelta(microseconds=1)),
                    WEBKIT_FORMAT: ("Webkit format", timedelta(microseconds=1)),
                    MAC_ABSOLUTE_TIME: ("Mac Absolute Time", timedelta(seconds=1)),
                    FILETIME: ("Windows FILETIME", timedelta(microseconds=1)),
                    SYSTEMTIME: ("Windows SYSTEMTIME", timedelta(microseconds=1000)),
                    DOS: ("DOS/FAT time", timedelta(seconds=2)),
                    OLE: ("OLE Automation Date", timedelta(microseconds=1))}
                    
  
  # Internal function to make a timestamp. For precision, separately calculates an integer and a float timestamp.
  def _make_timestamp(self, dt):
    td = dt - datetime(1970, 1, 1, tzinfo=pytz.utc)
    return td.days*24*60*60 + td.seconds, td.days*24*60*60 + td.seconds + float(td.microseconds)/1000000
    
  # Converts an UTC datetime to a specific timezone.
  def convert_to_timezone(self, dt, tz_name):
    tz = pytz.timezone(tz_name)
    new_dt = dt.astimezone(tz)
    return tz.normalize(new_dt)
  
  # Converts a timestamp to a Python datetime object.
  def convert_to_datetime(self, time_type, t):
    if time_type == self.UNIX: # Seconds after Jan 1 1970, midnight
      return datetime.fromtimestamp(int(t), pytz.utc)
    elif time_type == self.UNIX_DECIMAL: # Same except with fractional part
      return datetime.fromtimestamp(t, pytz.utc)
    elif time_type == self.JAVASCRIPT: # Milliseconds after Jan 1 1970, midnight
      unix = int(t / 1000)
      us = int(t % 1000) * 1000
      return datetime.fromtimestamp(unix, pytz.utc) + timedelta(microseconds=us)
    elif time_type == self.PRTIME: # Microseconds after Jan 1 1970, midnight
      unix = int(t / 1000000)
      us = int(t % 1000000)
      return datetime.fromtimestamp(unix, pytz.utc) + timedelta(microseconds=us)
    elif time_type == self.WEBKIT_FORMAT: # Microseconds after Jan 1 1601, midnight
      unix = int(t / 1000000) - 11644473600 
      us = int(t % 1000000)
      return datetime.fromtimestamp(unix, pytz.utc) + timedelta(microseconds=us)
    elif time_type == self.MAC_ABSOLUTE_TIME: # Microseconds after Jan 1 2001, midnight
      return datetime.fromtimestamp(int(t+978307200), pytz.utc) 
    elif time_type == self.FILETIME: # 100-nanosecond intervals after Jan 1 1601, midnight
      unix = int(t / 10000000) - 11644473600
      us = int((t % 10000000)/10)
      return datetime.fromtimestamp(unix, pytz.utc) + timedelta(microseconds=us)
    elif time_type == self.SYSTEMTIME: # year, month, day of week (sunday=0), day, hour, minute, second, millisecond, as two-byte little-endian integer
      up = struct.unpack("<HHHHHHHH", t)
      return datetime(up[0], up[1], up[3], up[4], up[5], up[6], up[7]*1000, tzinfo=pytz.utc)
    elif time_type == self.DOS: # seven bits year since 1980, four bits month, five bits day, five bits hour, six bits minute, five bits second/2
      up = struct.unpack(">L", t)[0]
      year = 1980 + (up >> 25)
      month = (up & 0b00000001111000000000000000000000) >> 21
      day = (up & 0b00000000000111110000000000000000) >> 16
      hour = (up & 0b00000000000000001111100000000000) >> 11
      minute = (up & 0b00000000000000000000011111100000) >> 5
      second = (up & 0b00000000000000000000000000011111) * 2
      return datetime(year, month, day, hour, minute, second)
    elif time_type == self.OLE: # days since 30 December 1899 midnight, with decimals
      return datetime(1899, 12, 30, 0, 0, 0, tzinfo=pytz.utc) + timedelta(days=t)
      
  # Converts a Python datetime to a timestamp.
  def convert_to_timestamp(self, time_type, dt):
    if time_type == self.UNIX:
      return self._make_timestamp(dt)[0]
    elif time_type == self.UNIX_DECIMAL:
      return self._make_timestamp(dt)[1]
    elif time_type == self.JAVASCRIPT:
      return self._make_timestamp(dt)[0] * 1000 + int(dt.microsecond/1000)
    elif time_type == self.PRTIME:
      return self._make_timestamp(dt)[0] * 1000000 + dt.microsecond
    elif time_type == self.WEBKIT_FORMAT:
      unix = self._make_timestamp(dt)[0]
      unix = (unix + 11644473600) * 1000000
      return unix + dt.microsecond
    elif time_type == self.MAC_ABSOLUTE_TIME:
      return self._make_timestamp(dt)[0]-978307200
    elif time_type == self.FILETIME:
      unix = self._make_timestamp(dt)[0]
      unix = (unix + 11644473600) * 10000000
      return unix + dt.microsecond*10
    elif time_type == self.SYSTEMTIME:
      weekday = dt.weekday() + 1
      if weekday == 7:
        weekday = 0
      return struct.pack("<HHHHHHHH", dt.year, dt.month, weekday, dt.day, dt.hour, dt.minute, dt.second, int(dt.microsecond/1000))
    elif time_type == self.DOS:
      b = (dt.year-1980) << 4
      b = (b + dt.month) << 5
      b = (b + dt.day) << 5
      b = (b + dt.hour) << 6
      b = (b + dt.minute) << 5
      b += int(dt.second/2)
      return struct.pack(">L", b)
    elif time_type == self.OLE:
      return float((dt - datetime(1899, 12, 30, 0, 0, 0, tzinfo=pytz.utc)).total_seconds())/86400


# Some test code.
if __name__ == "__main__":
  t = TimeConverter()
  test_datetime = datetime(2016, 5, 4, 3, 2, 1, 678901, tzinfo=pytz.utc)
  print "Reference time: %s" % test_datetime
  reference_berlin = t.convert_to_timezone(test_datetime, "Europe/Berlin")
  print "Converted to time zone Europe/Berlin: %s" % reference_berlin
  reference_auckland = t.convert_to_timezone(test_datetime, "Pacific/Auckland")
  print "Converted to time zone Pacific/Auckland: %s" % reference_auckland
  print ""
  
  timestamp_formats = t.TIMESTAMP_INFO.keys()
  timestamp_formats.sort()
  for tf in timestamp_formats:
    timestamp = t.convert_to_timestamp(tf, test_datetime)
    datetime_back = t.convert_to_datetime(tf, timestamp)
    name, precision = t.TIMESTAMP_INFO[tf]
    print name
    print "Precision: %s" % precision
    print "Reference time: %s" % test_datetime
    if isinstance(timestamp, int) or isinstance(timestamp, float):
      print "Converted: %s" % timestamp
    else:
      print "Converted: %s (hex)" % timestamp.encode("hex")
    print "Converted back: %s" % datetime_back
    print ""

