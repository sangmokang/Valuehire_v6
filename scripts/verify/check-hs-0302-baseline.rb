#!/usr/bin/env ruby
require 'digest'

repo = Dir.pwd
current = File.expand_path(ARGV.fetch(0, repo))
trusted_sha = '8c5494b637d6e97b5405c7fbaf381a3c9762e04b'
baseline_test_bytes = 7303
baseline_test_hash = '638789736b3b3f46576d56c1d752acefb0be35cd9fd25db3dffd105d56ee414a'
baseline_roster_bytes = 12712
baseline_roster_hash = '2e22f84ef27889ccf5ccdb46d5d68d7af5852cd605d12623f2393a9a1d389318'
baseline_required = 119
baseline_r5 = 7
test_path = 'humansearch/tests/test_hs_0302_r5_approved_root.py'
roster_path = 'scripts/verify/fixtures/hs-0302-required-tests.txt'
acceptance_path = 'scripts/acceptance-hs-0302.sh'

def current_file(root, path)
  File.binread(File.join(root, path))
rescue SystemCallError
  abort "VERDICT: NOT_RUN\nCURRENT_FILE: #{path} unavailable"
end

test = current_file(current, test_path)
roster_file = current_file(current, roster_path)
roster = roster_file.lines.reject { |line| line.strip.empty? || line.start_with?('#') }.map(&:strip)
script = current_file(current, acceptance_path)
r5 = script[/^MIN_R5_TESTS=(\d+)$/, 1]&.to_i
expected = script[/^EXPECTED_REQUIRED_IDS=(\d+)$/, 1]&.to_i
problems = []
problems << 'R5_TEST_PREFIX' unless test.bytesize >= baseline_test_bytes && Digest::SHA256.hexdigest(test.byteslice(0, baseline_test_bytes)) == baseline_test_hash
problems << 'REQUIRED_NODE_IDS' unless roster_file.bytesize >= baseline_roster_bytes && Digest::SHA256.hexdigest(roster_file.byteslice(0, baseline_roster_bytes)) == baseline_roster_hash
problems << 'MIN_R5_TESTS' unless baseline_r5 && r5 && r5 >= baseline_r5
problems << 'EXPECTED_REQUIRED_IDS' unless expected && expected >= baseline_required
problems << 'ROSTER_COUNT' unless expected == roster.length && roster.uniq.length == roster.length
if problems.empty?
  puts "VERDICT: PASS\nTRUSTED_SHA: #{trusted_sha}\nREQUIRED: #{baseline_required}->#{roster.length}"
else
  puts "VERDICT: FAIL\nTRUSTED_SHA: #{trusted_sha}\nWEAKENED: #{problems.join(',')}"
  exit 1
end
