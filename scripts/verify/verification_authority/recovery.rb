# frozen_string_literal: true

module VerificationAuthority
  class RecoveryJournal
    attr_reader :path

    def initialize(path)
      @path = path
    end

    def start
      write('status' => 'RECOVERING', 'completed' => [], 'pending' => %w[first second], 'attempts' => 0)
    end

    def read
      JSON.parse(File.read(path))
    end

    def write(data, fail_write = false)
      raise IOError, 'injected state write failure' if fail_write
      tmp = "#{path}.tmp"
      File.write(tmp, JSON.pretty_generate(data))
      File.rename(tmp, path)
      data
    end

    def delete_if_recovered
      data = read
      raise 'refusing to delete incomplete recovery state' unless data['status'] == 'RECOVERED'
      File.delete(path)
    end

    def run(events)
      start unless File.exist?(path)
      data = read
      data['attempts'] += 1
      return corrupt if events.include?('corrupt_state')
      finish_target(data, 'first')
      return 'SECOND_TARGET_FAILED' if events.include?('second_target_failure')
      return 'FORCED_TERMINATION' if events.include?('forced_termination')
      finish_target(data, 'second')
      return 'PERMISSION_RESTORE_FAILED' if events.include?('permission_restore_failure')
      return state_write_failure(data) if events.include?('state_write_failure')
      return 'RECOVERY_FAILED_AGAIN' if events.include?('recovery_failure_again')
      data['status'] = 'RECOVERED'
      write(data)
      delete_if_recovered
      'RECOVERED'
    rescue JSON::ParserError
      'CORRUPT'
    end

    private

    def corrupt
      File.write(path, '{partial')
      'CORRUPT'
    end

    def finish_target(data, target)
      return if data['completed'].include?(target)
      data['completed'] << target
      data['pending'].delete(target)
      write(data)
    end

    def state_write_failure(data)
      write(data, true)
      'UNEXPECTED_WRITE_SUCCESS'
    rescue IOError
      'STATE_WRITE_FAILED'
    end
  end

  module_function

  def recovery_case(events, expected, state_present)
    Dir.mktmpdir('verification-recovery-') do |tmp|
      journal = RecoveryJournal.new(File.join(tmp, 'state.json'))
      actual = journal.run(events)
      if events.include?('delete_attempt')
        begin
          journal.delete_if_recovered
        rescue StandardError
          actual = 'DELETE_REFUSED'
        end
      end
      present = File.exist?(journal.path)
      raise "recovery expected #{expected}, got #{actual}" unless actual == expected
      raise "recovery state presence expected=#{state_present} actual=#{present}" unless present == state_present
      [actual, present]
    end
  end

  def forced_termination_case
    Dir.mktmpdir('verification-recovery-signal-') do |tmp|
      journal = RecoveryJournal.new(File.join(tmp, 'state.json'))
      marker = File.join(tmp, 'first-written')
      pid = fork do
        journal.start
        state = journal.read
        state['completed'] << 'first'
        state['pending'].delete('first')
        journal.write(state)
        File.write(marker, 'ready')
        sleep 30
      end
      200.times do
        break if File.exist?(marker)
        sleep 0.01
      end
      raise 'forced termination child did not reach first durable write' unless File.exist?(marker)
      Process.kill('KILL', pid)
      Process.wait(pid)
      raise 'forced termination deleted recovery state' unless File.exist?(journal.path)
    end
    puts 'RECOVERY_CASE: forced_termination status=KILLED state_present=true'
  end

  def repeated_recovery_case
    Dir.mktmpdir('verification-recovery-repeat-') do |tmp|
      journal = RecoveryJournal.new(File.join(tmp, 'state.json'))
      first = journal.run(['second_target_failure'])
      second = journal.run([])
      third = journal.run([])
      valid = first == 'SECOND_TARGET_FAILED' && second == 'RECOVERED' && third == 'RECOVERED'
      raise 'repeated recovery contract failed' unless valid && !File.exist?(journal.path)
    end
    puts 'RECOVERY_CASE: repeated_recover status=RECOVERED state_present=false attempts=idempotent'
  end

  def recovery_fixtures(root)
    paths = Dir.glob(File.join(root, 'scripts/verify/fixtures/verification-authority/recovery/*.yaml')).sort
    raise 'recovery fixtures missing' if paths.empty?
    paths.each do |path|
      data, _text = yaml(path)
      if data['id'] == 'forced_termination'
        forced_termination_case
        next
      end
      actual, present = recovery_case(data['events'] || [], data['expected_status'], data['state_present'])
      puts "RECOVERY_CASE: #{data['id']} status=#{actual} state_present=#{present}"
    end
    repeated_recovery_case
    puts "RECOVERY_FIXTURES: total=#{paths.length + 1}"
    true
  end
end
