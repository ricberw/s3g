import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import optparse

parser = optparse.OptionParser()
parser.add_option("-i", "--inputfile", dest="input_file",
                  help="gcode file to read in", default=False)
parser.add_option("-o", "--outputfile", dest="output_file",
                  help="s3g file to write out", default=False)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
parser.add_option("-s", "--gcode_start_end_sequences", dest="start_end_sequences",
                  help="run gcode start and end proceeses", default=False)
(options, args) = parser.parse_args()


s = s3g.s3g()
s.writer = s3g.Writer.FileWriter(open(options.output_file, 'w'))

parser = s3g.Gcode.GcodeParser()
parser.state.values["build_name"] = 'test'
parser.state.profile = s3g.Profile(options.machine)
parser.s3g = s
profile = s3g.Profile('ReplicatorDual')
parser.state.profile = profile

environment = {}

if options.start_end_sequences:
  for line in parser.state.profile.values['print_start_sequence']:
    parser.ExecuteLine(line, environment)

with open(options.input_file) as f:
  for line in f:
    parser.ExecuteLine(line, environment)

if options.start_end_sequences:
  for line in parser.state.profile.values['print_end_sequence']:
    parser.ExecuteLine(line, environment)
