#!/usr/bin/env ruby
require 'fileutils'
require 'open3'
require 'tmpdir'

repo = File.expand_path('../..', __dir__)
checker = ARGV.fetch(0, File.join(repo, 'scripts/verify/check-hs-0302-baseline.rb'))
paths = %w[humansearch/tests/test_hs_0302_r5_approved_root.py
           scripts/verify/fixtures/hs-0302-required-tests.txt scripts/acceptance-hs-0302.sh]
missing_id = 'tests/test_hs_0302_r5_approved_root.py::test_other_db_filename_inside_approved_root_is_refused'

Dir.mktmpdir('hs0302-baseline-') do |tmp|
  paths.each do |path|
    dest = File.join(tmp, path)
    FileUtils.mkdir_p(File.dirname(dest))
    FileUtils.copy_file(File.join(repo, path), dest)
  end
  test = File.join(tmp, paths[0])
  roster = File.join(tmp, paths[1])
  acceptance = File.join(tmp, paths[2])
  originals = paths.map { |path| File.binread(File.join(tmp, path)) }
  cases = {
    'required test deletion' => [true, false, false],
    'roster deletion' => [false, true, false],
    'threshold reduction' => [false, false, true],
    'coordinated weakening' => [true, true, true],
  }
  out, _, status = Open3.capture3('ruby', checker, tmp, chdir: repo)
  abort "FAIL: positive baseline #{status.exitstatus} #{out}" unless status.success? && out.include?('VERDICT: PASS')
  cases.each do |label, (drop_test, drop_roster, lower_thresholds)|
    [test, roster, acceptance].zip(originals).each { |path, body| File.binwrite(path, body) }
    if drop_test
      body = File.binread(test)
      block = /^def test_other_db_filename_inside_approved_root_is_refused\(.*?(?=^def test_|\z)/m
      abort 'FAIL: test mutation anchor missing' unless body.match?(block)
      File.binwrite(test, body.sub(block, ''))
    end
    File.binwrite(roster, File.binread(roster).lines.reject { |line| line.strip == missing_id }.join) if drop_roster
    if lower_thresholds
      body = File.binread(acceptance).sub('MIN_R5_TESTS=7', 'MIN_R5_TESTS=6')
      body = body.sub(/EXPECTED_REQUIRED_IDS=(\d+)/) { "EXPECTED_REQUIRED_IDS=#{$1.to_i - 1}" }
      File.binwrite(acceptance, body)
    end
    out, _, status = Open3.capture3('ruby', checker, tmp, chdir: repo)
    abort "FAIL: #{label} survived #{status.exitstatus} #{out}" if status.success? || !out.include?('VERDICT: FAIL')
    puts "PASS: #{label} rejected"
  end
end
puts 'VERDICT: PASS'
