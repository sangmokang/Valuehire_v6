# frozen_string_literal: true

module VerificationAuthority
  MUTATION_DESCRIPTIONS = {
    'verifier_early_exit_zero' => 'verifier line 2 exits zero before checking',
    'ci_echo_command' => 'CI direct command is replaced with echo',
    'ci_comment_only' => 'CI command remains only as a comment',
    'ci_dead_code_before_command' => 'CI exits successfully before the verifier command',
    'artifact_sha_unbound' => 'artifact identity is no longer bound to the target SHA',
    'output_sha_comment_only' => 'output path is fixed while GITHUB_SHA remains only in a comment',
    'required_checker_deleted' => 'required checker file is deleted',
    'required_registry_renamed' => 'canonical requirements registry is renamed',
    'mutation_case_deleted' => 'one required mutation ID is deleted',
    'mutation_case_and_expected_count_lowered' => 'mutation ID and expected count are lowered together',
    'counterexample_emptied' => 'a requirement counterexample list is emptied',
    'verifier_wiring_removed' => 'verifier path text remains while execution wiring is removed',
    'manifest_and_checker_weakened' => 'protected manifest and checker inventory are weakened together',
    'authority_implicit_verified_backdoor' => 'candidate policy implicitly returns VERIFIED without return syntax',
    'mutation_runner_early_success' => 'mutation runner prints a forged summary and returns before cases run',
    'verified_sha_replaced_with_old_sha' => 'successful check SHA is replaced with an old SHA',
    'pr_head_sha_changed' => 'PR head moves while old evidence is reused',
    'required_check_name_changed' => 'required check name is changed',
    'workflow_identity_changed' => 'workflow identity is changed',
    'forged_success_fixture' => 'LLM report forges a successful GitHub check value',
    'rollback_permission_restore_failure' => 'permission restoration fails during rollback',
    'rollback_state_delete_attempt' => 'incomplete rollback tries to delete its state file',
    'normal_control' => 'clean isolated repository control'
  }.freeze

  module_function

  def mutation_copy(root)
    tmp = Dir.mktmpdir('verification-authority-mutation-')
    copy = File.join(tmp, 'repo')
    copy_tree(root, copy)
    env = clean_env.merge(
      'GIT_AUTHOR_NAME' => 'mutation-fixture',
      'GIT_AUTHOR_EMAIL' => 'mutation@example.invalid',
      'GIT_COMMITTER_NAME' => 'mutation-fixture',
      'GIT_COMMITTER_EMAIL' => 'mutation@example.invalid'
    )
    [%w[git init -q], %w[git add -A], %w[git commit -qm baseline]].each do |argv|
      _out, err, status = Open3.capture3(env, *argv, :chdir => copy)
      raise "mutation fixture git setup failed: #{err}" unless status.success?
    end
    [tmp, copy]
  end

  def replace!(path, before, after)
    text = File.read(path)
    raise "mutation target missing in #{path}: #{before.inspect}" unless text.include?(before)
    File.write(path, text.sub(before, after))
  end

  def run_mode(root, mode, *args)
    command(['ruby', 'scripts/verify/verification_authority.rb', mode] + args, root)
  end

  def status_from_output(output)
    output[/actual=([A-Z_]+)/, 1]
  end

  def result(command_text, expected, status, blocked)
    { 'command' => command_text, 'expected' => expected,
      'exit' => status ? status.exitstatus : 255, 'blocked' => blocked }
  end

  def mutation_group_files(id, copy)
    case id
    when 'verifier_early_exit_zero'
      path = File.join(copy, 'scripts/verify/verification_authority.rb')
      lines = File.readlines(path).insert(1, "exit 0\n")
      File.write(path, lines.join)
      out, _err, status = command(['bash', ACCEPTANCE], copy)
      result('bash scripts/acceptance-verification-authority.sh',
             'early verifier exit must fail the real acceptance and pre-push entrypoint', status,
             !(status && status.success?) && out.include?('VERIFIER_FAIL:'))
    when 'ci_echo_command'
      wf = File.join(copy, WORKFLOW)
      direct = "run: bash #{ACCEPTANCE} --output \"verification-results/verification-authority-${GITHUB_SHA}.json\""
      replace!(wf, direct, direct.sub('run: bash', 'run: echo bash'))
      out, _err, status = run_mode(copy, 'wiring-check')
      result('ruby scripts/verify/verification_authority.rb wiring-check', 'echo is not direct execution',
             status, !(status && status.success? && out.include?('WIRING:')))
    when 'ci_comment_only'
      wf = File.join(copy, WORKFLOW)
      replace!(wf, "      run: bash #{ACCEPTANCE}", "      # run: bash #{ACCEPTANCE}")
      out, _err, status = run_mode(copy, 'wiring-check')
      result('ruby scripts/verify/verification_authority.rb wiring-check',
             'comment-only command must not count as wiring', status,
             !(status && status.success? && out.include?('WIRING:')))
    when 'ci_dead_code_before_command'
      wf = File.join(copy, WORKFLOW)
      direct = "        run: bash #{ACCEPTANCE} --output \"verification-results/verification-authority-${GITHUB_SHA}.json\""
      replace!(wf, direct, "        run: |\n          exit 0\n#{direct.sub('        run: ', '          ')}")
      _out, _err, status = run_mode(copy, 'wiring-check')
      result('ruby scripts/verify/verification_authority.rb wiring-check',
             'an earlier successful exit must make the verifier dead code', status, !(status && status.success?))
    when 'artifact_sha_unbound'
      wf = File.join(copy, WORKFLOW)
      replace!(wf, 'name: verification-authority-${{ github.sha }}', 'name: verification-authority-old-sha')
      _out, _err, status = run_mode(copy, 'wiring-check')
      result('ruby scripts/verify/verification_authority.rb wiring-check',
             'artifact name and path must both bind to github.sha', status, !(status && status.success?))
    when 'output_sha_comment_only'
      wf = File.join(copy, WORKFLOW)
      direct = "        run: bash #{ACCEPTANCE} --output \"verification-results/verification-authority-${GITHUB_SHA}.json\""
      replace!(wf, direct, "        run: |\n          # GITHUB_SHA is not bound to output\n#{direct.sub('${GITHUB_SHA}', 'fixed-name')}")
      _out, _err, status = run_mode(copy, 'wiring-check')
      result('ruby scripts/verify/verification_authority.rb wiring-check',
             'GITHUB_SHA in a comment must not validate a fixed output path', status, !(status && status.success?))
    when 'required_checker_deleted'
      File.delete(File.join(copy, 'scripts/verify/verification_authority.rb'))
      _out, _err, status = run_mode(copy, 'contract-self-test')
      result('ruby scripts/verify/verification_authority.rb contract-self-test',
             'deleted checker cannot validate', status, !(status && status.success?))
    when 'required_registry_renamed'
      File.rename(File.join(copy, CONTRACT), File.join(copy, "#{CONTRACT}.renamed"))
      _out, _err, status = run_mode(copy, 'contract-self-test')
      result('ruby scripts/verify/verification_authority.rb contract-self-test',
             'canonical registry name is required', status, !(status && status.success?))
    end
  end

  def mutation_group_contract(id, copy)
    case id
    when 'mutation_case_deleted', 'mutation_case_and_expected_count_lowered'
      path = File.join(copy, CONTRACT)
      replace!(path, "mutation_expected_count: 23\n", "mutation_expected_count: 22\n") if id.include?('expected_count')
      replace!(path, "  - ci_echo_command\n", '')
      _out, _err, status = run_mode(copy, 'mutation-catalog-check')
      expected = id.include?('expected_count') ? 'lowering case and count together must fail intrinsic inventory' : 'required mutation ID deletion must fail'
      result('ruby scripts/verify/verification_authority.rb mutation-catalog-check', expected,
             status, !(status && status.success?))
    when 'counterexample_emptied'
      path = File.join(copy, CONTRACT)
      text = File.read(path)
      mutated = text.sub(/    counterexamples:\n(?:      - .*\n)+    verifier:/, "    counterexamples: []\n    verifier:")
      raise 'counterexample mutation target missing' if mutated == text
      File.write(path, mutated)
      _out, _err, status = run_mode(copy, 'contract-self-test')
      result('ruby scripts/verify/verification_authority.rb contract-self-test',
             'empty counterexample must fail closed schema', status, !(status && status.success?))
    when 'verifier_wiring_removed'
      wf = File.join(copy, WORKFLOW)
      replace!(wf, "      run: bash #{ACCEPTANCE}", "      run: true # #{ACCEPTANCE} path remains only as text")
      _out, _err, status = run_mode(copy, 'wiring-check')
      result('ruby scripts/verify/verification_authority.rb wiring-check',
             'path existence without an executed stage must fail', status, !(status && status.success?))
    when 'manifest_and_checker_weakened'
      manifest = File.join(copy, MANIFEST)
      text = File.read(manifest)
      text.sub!(/  - path: \.github\/workflows\/verify\.yml\n    category: trusted_workflow_candidate\n    required: true\n/, '')
      File.write(manifest, text)
      checker = File.join(copy, 'scripts/verify/verification_authority.rb')
      replace!(checker, '.github/workflows/verify.yml ', '')
      _out, _err, status = run_mode(copy, 'protected-check')
      result('ruby scripts/verify/verification_authority.rb protected-check',
             'contract inventory must catch manifest and checker joint weakening', status,
             !(status && status.success?))
    when 'authority_implicit_verified_backdoor'
      checker = File.join(copy, 'scripts/verify/verification_authority.rb')
      replace!(checker, "    'LOCAL_CANDIDATE'\n  end\n\n  def sha_one",
               "    evidence['run_identity'] == 'trusted-override' ? 'VERIFIED' : 'LOCAL_CANDIDATE'\n  end\n\n  def sha_one")
      _out, _err, status = run_mode(copy, 'authority-check')
      result('ruby scripts/verify/verification_authority.rb authority-check',
             'implicit official-state backdoor must fail candidate-policy inspection', status,
             !(status && status.success?))
    when 'mutation_runner_early_success'
      runner = File.join(copy, 'scripts/verify/verification_authority/mutations.rb')
      replace!(runner, "  def mutations(root)\n",
               "  def mutations(root)\n    puts 'MUTATIONS: total=23 blocked=22 survived=0 controls=1'\n    return true\n")
      _out, _err, status = command(['bash', ACCEPTANCE], copy)
      result('bash scripts/acceptance-verification-authority.sh',
             'forged mutation summary without per-case evidence must fail the outer verifier', status,
             !(status && status.success?))
    end
  end

  def sha_mutation_result(copy, fixture, expected_state, reason)
    relative = "scripts/verify/fixtures/verification-authority/sha/#{fixture}"
    out, _err, status = run_mode(copy, 'sha-one', relative)
    result("ruby scripts/verify/verification_authority.rb sha-one #{relative}", reason,
           status, status && status.success? && status_from_output(out) == expected_state)
  end

  def mutation_group_sha(id, copy)
    case id
    when 'verified_sha_replaced_with_old_sha'
      sha_mutation_result(copy, '02-old-check-sha.yaml', 'STALE', 'old successful check must become STALE')
    when 'pr_head_sha_changed'
      sha_mutation_result(copy, '03-pr-head-changed.yaml', 'STALE', 'changed PR head must make old evidence STALE')
    when 'required_check_name_changed'
      sha_mutation_result(copy, '04-check-name-mismatch.yaml', 'FAIL', 'required check mismatch must FAIL')
    when 'workflow_identity_changed'
      sha_mutation_result(copy, '05-workflow-mismatch.yaml', 'FAIL', 'workflow identity mismatch must FAIL')
    when 'forged_success_fixture'
      sha_mutation_result(copy, '09-forged-success.yaml', 'FAIL', 'LLM or local forged success must FAIL authority source')
    end
  end

  def mutation_group_recovery(id, copy)
    case id
    when 'rollback_permission_restore_failure'
      out, _err, status = run_mode(copy, 'recovery-one', 'permission_restore_failure')
      result('ruby scripts/verify/verification_authority.rb recovery-one permission_restore_failure',
             'permission restore failure must retain state', status,
             status && status.success? && out.include?('state_present=true'))
    when 'rollback_state_delete_attempt'
      out, _err, status = run_mode(copy, 'recovery-one', 'delete_attempt')
      valid = status && status.success? && out.include?('DELETE_REFUSED') && out.include?('state_present=true')
      result('ruby scripts/verify/verification_authority.rb recovery-one delete_attempt',
             'incomplete rollback state deletion must be refused', status, valid)
    when 'normal_control'
      out, _err, status = run_mode(copy, 'verify-all', '--no-mutations')
      result('ruby scripts/verify/verification_authority.rb verify-all --no-mutations',
             'clean control must run all non-recursive checks', status,
             status && status.success? && out.include?('AUTHORITY_RESULT: LOCAL_CANDIDATE'))
    end
  end

  def execute_mutation_case(id, copy)
    return mutation_group_files(id, copy) if REQUIRED_MUTATIONS[0, 8].include?(id)
    return mutation_group_contract(id, copy) if REQUIRED_MUTATIONS[8, 7].include?(id)
    return mutation_group_sha(id, copy) if REQUIRED_MUTATIONS[15, 5].include?(id)
    mutation_group_recovery(id, copy)
  end

  def mutation_summary_from(output)
    REQUIRED_MUTATIONS.each do |id|
      label = id == 'normal_control' ? 'CONTROL_OK' : 'BLOCKED'
      raise "mutation case evidence missing #{id}" unless output.include?("#{label}: #{id}\n")
      unless output.include?("original_repository_unchanged[#{id}]: true")
        raise "mutation isolation evidence missing #{id}"
      end
    end
    match = output.match(/MUTATIONS: total=(\d+) blocked=(\d+) survived=(\d+) controls=(\d+)/)
    raise 'mutation summary missing from executed verifier output' unless match
    values = match.captures.map(&:to_i)
    expected = [REQUIRED_MUTATIONS.length, REQUIRED_MUTATIONS.length - 1, 0, 1]
    raise "mutation summary mismatch actual=#{values.join(',')} expected=#{expected.join(',')}" unless values == expected
    { 'total' => values[0], 'blocked' => values[1], 'survived' => values[2], 'controls' => values[3] }
  end

  def structural_limit_check(root)
    tmp, copy = mutation_copy(root)
    manifest = File.join(copy, MANIFEST)
    text = File.read(manifest).sub(/  - path: \.github\/workflows\/verify\.yml\n    category: trusted_workflow_candidate\n    required: true\n/, '')
    File.write(manifest, text)
    replace!(File.join(copy, 'scripts/verify/verification_authority.rb'), '.github/workflows/verify.yml ', '')
    contract = File.join(copy, CONTRACT)
    replace!(contract, "protected_surface:\n  - .github/workflows/verify.yml\n", "protected_surface:\n")
    out, err, status = run_mode(copy, 'protected-check')
    raise "three-way structural limit did not survive: #{out}#{err}" unless status&.success? && out.include?('paths=11')
    puts 'STRUCTURAL_LIMIT: three_way_survived=true enforcement=DETECT_ONLY original_unchanged=true'
    true
  ensure
    FileUtils.remove_entry(tmp) if tmp && File.exist?(tmp)
  end

  def mutations(root)
    before, _err, before_status = command(%w[git status --porcelain=v1], root)
    raise 'cannot snapshot original status' unless before_status && before_status.success?
    results = REQUIRED_MUTATIONS.map do |id|
      tmp, copy = mutation_copy(root)
      control = id == 'normal_control'
      begin
        value = execute_mutation_case(id, copy)
      rescue StandardError => e
        value = { 'command' => '', 'expected' => "harness error: #{e.class}: #{e.message}", 'exit' => 255, 'blocked' => false }
      ensure
        FileUtils.remove_entry(tmp) if tmp && File.exist?(tmp)
      end
      value.merge('id' => id, 'control' => control)
    end
    print_mutation_results(results)
    after, _after_err, after_status = command(%w[git status --porcelain=v1], root)
    unchanged = after_status && after_status.success? && before == after
    results.each { |entry| puts "  original_repository_unchanged[#{entry['id']}]: #{unchanged}" }
    enforce_mutation_summary(results, unchanged)
  end

  def print_mutation_results(results)
    results.each do |entry|
      label = entry['control'] ? (entry['blocked'] ? 'CONTROL_OK' : 'CONTROL_FAIL') : (entry['blocked'] ? 'BLOCKED' : 'SURVIVED')
      puts "#{label}: #{entry['id']}"
      puts "  broke: #{MUTATION_DESCRIPTIONS.fetch(entry['id'])}"
      puts "  command: #{entry['command']}"
      puts "  actual_exit: #{entry['exit']}"
      puts "  expected: #{entry['expected']}"
      puts "  survived: #{entry['control'] ? 'not_applicable' : (!entry['blocked']).to_s}"
    end
  end

  def enforce_mutation_summary(results, unchanged)
    mutations_only = results.reject { |entry| entry['control'] }
    blocked = mutations_only.count { |entry| entry['blocked'] }
    survived = mutations_only.length - blocked
    controls = results.count { |entry| entry['control'] && entry['blocked'] }
    puts "MUTATIONS: total=#{results.length} blocked=#{blocked} survived=#{survived} controls=#{controls}"
    raise 'mutation harness changed original repository' unless unchanged
    valid = survived.zero? && controls == 1 && results.length == REQUIRED_MUTATIONS.length
    raise "VERIFIER_FAIL: survived=#{survived} controls=#{controls}" unless valid
    true
  end
end
