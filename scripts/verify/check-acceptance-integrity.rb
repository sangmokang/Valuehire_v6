#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "json"
require "pathname"

CONTRACT_PATH = "docs/sot/acceptance-integrity-contract.json"
EXPECTED_CONTRACT_SHA256 = "91acd80b3ce5299b4e5fa40daa852b2c76ff651576053fa52a2aaa51319b6d69"
EXPECTED_COUNT = 27

def verdict(kind, message, code)
  puts "#{kind}: #{message}"
  puts "CHECKED: 0"
  exit code
end

def not_run(message)
  verdict("VERDICT: NOT_RUN", message, 2)
end

def fail_closed(message)
  verdict("VERDICT: FAIL", message, 1)
end

class JsonDuplicateKeyScanner
  def initialize(source)
    @source = source
    @index = 0
  end

  def scan
    skip_ws
    scan_value
    skip_ws
    raise JSON::ParserError, "trailing JSON input" unless @index == @source.length
  end

  private

  def scan_value
    skip_ws
    case @source[@index]
    when "{" then scan_object
    when "[" then scan_array
    when "\"" then scan_string
    else scan_scalar
    end
  end

  def scan_object
    @index += 1
    skip_ws
    return @index += 1 if @source[@index] == "}"

    seen = {}
    loop do
      key = scan_string
      raise JSON::ParserError, "duplicate object key #{key.inspect}" if seen[key]
      seen[key] = true
      skip_ws
      expect(":")
      scan_value
      skip_ws
      break if consume("}")
      expect(",")
      skip_ws
    end
  end

  def scan_array
    @index += 1
    skip_ws
    return @index += 1 if @source[@index] == "]"

    loop do
      scan_value
      skip_ws
      break if consume("]")
      expect(",")
      skip_ws
    end
  end

  def scan_string
    start = @index
    expect("\"")
    loop do
      char = @source[@index]
      raise JSON::ParserError, "unterminated JSON string" if char.nil?
      @index += (char == "\\" ? 2 : 1)
      break if char == "\""
    end
    JSON.parse(@source[start...@index])
  end

  def scan_scalar
    start = @index
    @index += 1 while @source[@index] && @source[@index] !~ /[\s,}\]]/
    raise JSON::ParserError, "empty JSON value" if start == @index
  end

  def skip_ws
    @index += 1 while @source[@index] =~ /\s/
  end

  def consume(token)
    return false unless @source[@index] == token
    @index += 1
    true
  end

  def expect(token)
    raise JSON::ParserError, "missing JSON token #{token.inspect}" unless consume(token)
  end
end

def canonical_path!(path, label)
  not_run("#{label} path is empty") unless path.is_a?(String) && !path.empty?
  not_run("#{label} path must be repo-relative") if path.start_with?("/", "~")
  parts = path.split("/")
  not_run("#{label} path escapes repository") if parts.include?("..")
  clean = Pathname.new(path).cleanpath.to_s
  not_run("#{label} path is not canonical: #{path}") unless clean == path && path != "."
  path
end

def tracked_regular!(path, label)
  canonical_path!(path, label)
  not_run("#{label} is not tracked: #{path}") unless system("git", "ls-files", "--error-unmatch", "--", path, out: File::NULL, err: File::NULL)
  begin
    lst = File.lstat(path)
    st = File.stat(path)
  rescue SystemCallError => error
    not_run("#{label} stat failed: #{path} #{error.class}")
  end
  not_run("#{label} is a symlink: #{path}") if lst.symlink?
  not_run("#{label} is not a regular file: #{path}") unless st.file?
  not_run("#{label} is hardlinked: #{path}") unless st.nlink == 1
end

def load_contract
  tracked_regular!(CONTRACT_PATH, "contract")
  source = File.binread(CONTRACT_PATH)
  JsonDuplicateKeyScanner.new(source).scan
  contract = JSON.parse(source)
  validate_contract!(contract)
  actual = Digest::SHA256.hexdigest(source)
  not_run("contract digest mismatch") unless actual == EXPECTED_CONTRACT_SHA256
  contract
rescue JSON::ParserError => error
  not_run("contract parse failed: #{error.message.lines.first.to_s.strip}")
end

def validate_contract!(contract)
  keys = %w[algorithm inventory schema_version]
  not_run("contract root schema invalid") unless contract.is_a?(Hash) && contract.keys.sort == keys
  not_run("contract schema_version invalid") unless contract["schema_version"] == 1
  not_run("contract algorithm invalid") unless contract["algorithm"] == "sha256"
  inventory = contract["inventory"]
  not_run("inventory is empty") unless inventory.is_a?(Array) && !inventory.empty?
  not_run("inventory count mismatch") unless inventory.length == EXPECTED_COUNT

  paths = []
  inventory.each_with_index do |entry, index|
    not_run("inventory entry #{index} schema invalid") unless entry.is_a?(Hash) && entry.keys.sort == %w[path sha256]
    path = canonical_path!(entry["path"], "inventory entry #{index}")
    digest = entry["sha256"]
    not_run("inventory digest invalid for #{path}") unless digest.is_a?(String) && digest.match?(/\A[0-9a-f]{64}\z/)
    paths << path
  end
  not_run("inventory has duplicate paths") unless paths.uniq.length == paths.length
  not_run("inventory must be sorted") unless paths == paths.sort
end

target = ARGV.fetch(0) { not_run("target argument missing") }
canonical_path!(target, "target")
contract = load_contract
entry = contract.fetch("inventory").find { |item| item["path"] == target }
not_run("target is not approved: #{target}") unless entry
tracked_regular!(target, "target")
actual_target = Digest::SHA256.file(target).hexdigest
fail_closed("target content mismatch: #{target}") unless actual_target == entry.fetch("sha256")

puts "PASS(acceptance-integrity): #{target}"
puts "CHECKED: 1"
