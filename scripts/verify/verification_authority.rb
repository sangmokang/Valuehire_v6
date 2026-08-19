#!/usr/bin/env ruby
# frozen_string_literal: true

require 'digest'
require 'fileutils'
require 'json'
require 'open3'
require 'psych'
require 'shellwords'
require 'tmpdir'
require_relative 'verification_authority/recovery'
require_relative 'verification_authority/mutations'

module VerificationAuthority
  GIT_ENV = %w[
    GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR
    GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
  ].freeze
  CONTRACT = 'docs/sot/verification-requirements.yaml'.freeze
  MANIFEST = 'docs/sot/verification-protected-surface.yaml'.freeze
  WORKFLOW = '.github/workflows/verify.yml'.freeze
  ACCEPTANCE = 'scripts/acceptance-verification-authority.sh'.freeze
  REQUIRED_CHECK = 'verify'.freeze
  WORKFLOW_IDENTITY = '.github/workflows/verify.yml@verify'.freeze
  ROOT_KEYS = %w[
    schema_version required_check workflow_identity mutation_expected_count
    mutation_catalog protected_surface unregistered_requirements requirements
  ].freeze
  REQUIREMENT_KEYS = %w[
    id invariant counterexamples verifier stage authority coverage_status
  ].freeze
  STAGES = %w[local pre-push ci policy].freeze
  AUTHORITIES = %w[implementer_candidate external_policy_gate].freeze
  COVERAGE = %w[COVERED MANUAL UNREGISTERED BLOCKED].freeze
  VERIFIER_MARKERS = { 'VA-001' => 'AUTHORITY:', 'VA-002' => 'CONTRACT_SELF_TEST:',
                       'VA-003' => 'WIRING:', 'VA-004' => 'MUTATIONS:', 'VA-005' => 'SHA_FIXTURES:',
                       'VA-006' => 'RECOVERY_FIXTURES:', 'VA-007' => 'DERIVED_STATE:',
                       'VA-008' => 'STRUCTURAL_LIMIT:' }.freeze
  REQUIRED_MUTATIONS = %w[
    verifier_early_exit_zero ci_echo_command
    ci_comment_only
    ci_dead_code_before_command artifact_sha_unbound output_sha_comment_only
    required_checker_deleted
    required_registry_renamed
    mutation_case_deleted
    mutation_case_and_expected_count_lowered
    counterexample_emptied
    verifier_wiring_removed
    manifest_and_checker_weakened authority_implicit_verified_backdoor mutation_runner_early_success
    verified_sha_replaced_with_old_sha
    pr_head_sha_changed
    required_check_name_changed
    workflow_identity_changed
    forged_success_fixture
    rollback_permission_restore_failure
    rollback_state_delete_attempt
    normal_control
  ].freeze

  INTRINSIC_PROTECTED = %w[
    .github/workflows/verify.yml docs/sot/verification-authority.md
    docs/sot/verification-requirements.yaml docs/sot/verification-protected-surface.yaml
    scripts/verify/verification_authority.rb scripts/verify/verification_authority/mutations.rb
    scripts/verify/verification_authority/recovery.rb scripts/verify/run-verification-authority-mutations.sh
    scripts/acceptance-verification-authority.sh hooks/pre-push docs/sot/git-workflow.md
    docs/sot/verification-commands.md
  ].freeze
  module_function

  def clean_env
    GIT_ENV.each_with_object({}) { |key, env| env[key] = nil }
  end

  def command(command, root)
    argv = command.is_a?(Array) ? command : Shellwords.split(command)
    Open3.capture3(clean_env, *argv, :chdir => root)
  rescue StandardError => e
    ['', "#{e.class}: #{e.message}\n", nil]
  end

  def repo_root(start = Dir.pwd)
    out, _err, status = Open3.capture3(clean_env, 'git', 'rev-parse', '--show-toplevel', :chdir => start)
    abort('NOT_RUN: git repository unavailable') unless status.success?
    out.strip
  end

  def duplicate_keys!(node, path = '$')
    case node
    when Psych::Nodes::Mapping
      seen = {}
      node.children.each_slice(2) do |key, value|
        label = key.respond_to?(:value) ? key.value : key.to_s
        raise "duplicate YAML key #{path}.#{label}" if seen[label]
        seen[label] = true
        duplicate_keys!(value, "#{path}.#{label}")
      end
    when Psych::Nodes::Sequence
      node.children.each_with_index { |child, index| duplicate_keys!(child, "#{path}[#{index}]") }
    end
  end

  def yaml(path)
    text = File.read(path)
    stream = Psych.parse_stream(text, path)
    stream.children.each { |doc| duplicate_keys!(doc.root) if doc.root }
    data = Psych.safe_load(text, [], [], false)
    [data, text]
  rescue Psych::Exception => e
    raise "YAML parse failure #{path}: #{e.message}"
  end

  def nonempty_string?(value)
    value.is_a?(String) && !value.strip.empty?
  end

  def exact_keys!(hash, allowed, label)
    raise "#{label} must be a mapping" unless hash.is_a?(Hash)
    actual = hash.keys.map(&:to_s).sort
    expected = allowed.sort
    extra = actual - expected
    missing = expected - actual
    raise "#{label} unknown fields: #{extra.join(',')}" unless extra.empty?
    raise "#{label} missing fields: #{missing.join(',')}" unless missing.empty?
  end

  def validate_command!(verifier, root)
    argv = Shellwords.split(verifier)
    raise 'verifier command is empty' if argv.empty?
    raise "verifier executable not allowed: #{argv[0]}" unless %w[ruby bash].include?(argv[0])
    raise 'verifier script path missing' unless argv[1]
    path = File.expand_path(argv[1], root)
    root_prefix = File.expand_path(root) + File::SEPARATOR
    raise 'verifier escapes repository root' unless path.start_with?(root_prefix)
    raise "verifier script does not exist: #{argv[1]}" unless File.file?(path)
  end

  def load_contract(root)
    path = File.join(root, CONTRACT)
    data, _text = yaml(path)
    exact_keys!(data, ROOT_KEYS, 'contract root')
    raise 'schema_version must be 1' unless data['schema_version'] == 1
    raise 'required_check mismatch' unless data['required_check'] == REQUIRED_CHECK
    raise 'workflow_identity mismatch' unless data['workflow_identity'] == WORKFLOW_IDENTITY
    raise 'requirements must be a non-empty list' unless data['requirements'].is_a?(Array) && !data['requirements'].empty?
    raise 'mutation_catalog must be a list' unless data['mutation_catalog'].is_a?(Array)
    raise 'protected_surface must be a list' unless data['protected_surface'].is_a?(Array)
    raise 'unregistered_requirements must be a list' unless data['unregistered_requirements'].is_a?(Array)

    ids = {}
    data['requirements'].each_with_index do |entry, index|
      exact_keys!(entry, REQUIREMENT_KEYS, "requirements[#{index}]")
      REQUIREMENT_KEYS.each do |key|
        next if %w[counterexamples stage].include?(key)
        raise "requirements[#{index}].#{key} is empty" unless nonempty_string?(entry[key])
      end
      raise "requirements[#{index}].counterexamples is empty" unless entry['counterexamples'].is_a?(Array) && !entry['counterexamples'].empty?
      entry['counterexamples'].each do |counterexample|
        raise "requirements[#{index}] has empty counterexample" unless nonempty_string?(counterexample)
      end
      raise "requirements[#{index}].stage is empty" unless entry['stage'].is_a?(Array) && !entry['stage'].empty?
      bad_stages = entry['stage'] - STAGES
      raise "requirements[#{index}] unknown stages: #{bad_stages.join(',')}" unless bad_stages.empty?
      raise "requirements[#{index}] duplicate stages" unless entry['stage'].uniq.length == entry['stage'].length
      raise "requirements[#{index}] authority invalid" unless AUTHORITIES.include?(entry['authority'])
      raise "requirements[#{index}] coverage_status invalid" unless COVERAGE.include?(entry['coverage_status'])
      if entry['stage'].include?('policy') && entry['coverage_status'] != 'BLOCKED'
        raise "requirements[#{index}] policy stage must be BLOCKED until external enforcement exists"
      end
      raise "duplicate requirement id #{entry['id']}" if ids[entry['id']]
      ids[entry['id']] = true
      validate_command!(entry['verifier'], root)
    end
    data
  end

  def contract_self_test(root)
    load_contract(root)
    mutations = {
      'duplicate_field' => lambda do |text|
        text.sub("    invariant: LLM and implementer reports cannot create VERIFIED; protected-surface changes require policy review.\n", "    invariant: duplicate\n    invariant: LLM and implementer reports cannot create VERIFIED; protected-surface changes require policy review.\n")
      end,
      'unknown_field' => lambda do |text|
        text.sub("    authority: external_policy_gate\n", "    unexpected_field: forbidden\n    authority: external_policy_gate\n")
      end,
      'missing_verifier' => lambda do |text|
        text.sub('ruby scripts/verify/verification_authority.rb authority-check', 'ruby scripts/verify/missing-authority-check.rb')
      end,
      'empty_invariant' => lambda do |text|
        text.sub('    invariant: LLM and implementer reports cannot create VERIFIED; protected-surface changes require policy review.', "    invariant: ''")
      end,
      'unknown_stage' => lambda do |text|
        text.sub("      - policy\n", "      - unknown-stage\n")
      end,
      'uncovered_policy_stage' => lambda do |text|
        text.sub("    coverage_status: BLOCKED\n", "    coverage_status: COVERED\n")
      end
    }
    original = File.read(File.join(root, CONTRACT))
    mutations.each do |name, transform|
      Dir.mktmpdir("contract-self-test-#{name}-") do |tmp|
        copy = File.join(tmp, 'repo')
        copy_tree(root, copy)
        path = File.join(copy, CONTRACT)
        changed = transform.call(File.read(path))
        raise "contract self-test mutation did not change #{name}" if changed == File.read(path)
        File.write(path, changed)
        begin
          load_contract(copy)
          raise "contract self-test mutation survived #{name}"
        rescue StandardError => e
          raise if e.message.start_with?('contract self-test mutation survived')
        end
      end
    end
    raise 'contract self-test changed original registry' unless File.read(File.join(root, CONTRACT)) == original
    puts "CONTRACT_SELF_TEST: negative_cases=#{mutations.length} blocked=#{mutations.length}"
    true
  end

  def contract_check(root, execute, skip_mutations)
    contract = load_contract(root)
    outputs = []
    if execute
      contract['requirements'].each do |entry|
        if skip_mutations && entry['id'] == 'VA-004'
          outputs << "SKIPPED_INTERNAL: #{entry['id']} mutation recursion guard"
          next
        end
        out, err, status = command(entry['verifier'], root)
        rc = status ? status.exitstatus : 255
        outputs << "$ #{entry['verifier']}\n#{out}#{err}EXIT=#{rc}"
        raise "verifier failed #{entry['id']} exit=#{rc}" unless status && status.success?
      end
    end
    puts "CONTRACT: requirements=#{contract['requirements'].length} executed=#{execute ? contract['requirements'].length - (skip_mutations ? 1 : 0) : 0} unregistered=#{contract['unregistered_requirements'].length}"
    outputs.each { |output| puts output }
    contract
  end

  def mutation_catalog_check(root)
    contract = load_contract(root)
    catalog = contract['mutation_catalog']
    raise 'mutation catalog contains duplicates' unless catalog.uniq.length == catalog.length
    raise "mutation expected count #{contract['mutation_expected_count']} != #{REQUIRED_MUTATIONS.length}" unless contract['mutation_expected_count'] == REQUIRED_MUTATIONS.length
    missing = REQUIRED_MUTATIONS - catalog
    extra = catalog - REQUIRED_MUTATIONS
    raise "mutation catalog mismatch missing=#{missing.join(',')} extra=#{extra.join(',')}" unless missing.empty? && extra.empty?
    puts "MUTATION_CATALOG: #{catalog.length}/#{REQUIRED_MUTATIONS.length}"
    true
  end

  def protected_check(root)
    contract = load_contract(root)
    data, _text = yaml(File.join(root, MANIFEST))
    exact_keys!(data, %w[schema_version enforcement paths external_controls], 'protected manifest root')
    raise 'protected manifest schema_version must be 1' unless data['schema_version'] == 1
    raise 'internal protection must be DETECT_ONLY' unless data['enforcement'] == 'DETECT_ONLY'
    raise 'protected paths must be non-empty' unless data['paths'].is_a?(Array) && !data['paths'].empty?
    paths = data['paths'].map.with_index do |entry, index|
      exact_keys!(entry, %w[path category required], "protected paths[#{index}]")
      raise "protected path #{index} empty" unless nonempty_string?(entry['path'])
      raise "protected category #{index} empty" unless nonempty_string?(entry['category'])
      raise "protected required #{index} must be boolean" unless [true, false].include?(entry['required'])
      raise "required protected file missing #{entry['path']}" if entry['required'] && !File.file?(File.join(root, entry['path']))
      entry['path']
    end
    raise 'protected path duplicates' unless paths.uniq.length == paths.length
    raise 'manifest differs from intrinsic protected inventory' unless paths.sort == INTRINSIC_PROTECTED.sort
    raise 'contract differs from intrinsic protected inventory' unless contract['protected_surface'].sort == INTRINSIC_PROTECTED.sort
    raise 'external_controls must be non-empty' unless data['external_controls'].is_a?(Array) && !data['external_controls'].empty?
    data['external_controls'].each_with_index do |entry, index|
      exact_keys!(entry, %w[control status evidence authority], "external_controls[#{index}]")
      raise "external control #{index} invalid status" unless %w[ENFORCED DETECT_ONLY UNAVAILABLE BLOCKED].include?(entry['status'])
      %w[control evidence authority].each do |key|
        raise "external control #{index}.#{key} empty" unless nonempty_string?(entry[key])
      end
    end
    puts "PROTECTED: paths=#{paths.length} enforcement=DETECT_ONLY external=#{data['external_controls'].length}"
    true
  end

  def executable_lines(run)
    run.to_s.lines.map(&:strip).reject { |line| line.empty? || line.start_with?('#') }
  end

  def direct_acceptance_line?(line)
    argv = Shellwords.split(line)
    argv == ['bash', ACCEPTANCE, '--output', 'verification-results/verification-authority-${GITHUB_SHA}.json']
  rescue ArgumentError
    false
  end

  def copy_tree(source, destination)
    FileUtils.mkdir_p(destination)
    Dir.children(source).each do |entry|
      next if entry == '.git' || entry == 'worktrees'
      FileUtils.cp_r(File.join(source, entry), destination, :preserve => true)
    end
  end

  def prepush_runtime_wiring(root)
    Dir.mktmpdir('verification-authority-wiring-') do |tmp|
      repo = File.join(tmp, 'repo')
      copy_tree(root, repo)
      marker = File.join(tmp, 'acceptance-executed')
      Dir.glob(File.join(repo, 'scripts', 'acceptance-*.sh')).each do |path|
        File.write(path, "#!/usr/bin/env bash\nexit 0\n")
        FileUtils.chmod(0o755, path)
      end
      File.write(File.join(repo, 'verify.sh'), "#!/usr/bin/env bash\nexit 0\n")
      FileUtils.chmod(0o755, File.join(repo, 'verify.sh'))
      target = File.join(repo, ACCEPTANCE)
      File.write(target, "#!/usr/bin/env bash\nprintf executed > \"$VA_WIRING_MARKER\"\nexit 0\n")
      FileUtils.chmod(0o755, target)

      env = clean_env.merge(
        'GIT_AUTHOR_NAME' => 'verification-fixture',
        'GIT_AUTHOR_EMAIL' => 'verification@example.invalid',
        'GIT_COMMITTER_NAME' => 'verification-fixture',
        'GIT_COMMITTER_EMAIL' => 'verification@example.invalid'
      )
      commands = [
        %w[git init -q],
        %w[git add -A],
        %w[git commit -qm fixture]
      ]
      commands.each do |argv|
        _out, err, status = Open3.capture3(env, *argv, :chdir => repo)
        raise "pre-push fixture setup failed: #{err}" unless status.success?
      end
      run_env = env.merge('VA_WIRING_MARKER' => marker)
      out, err, status = Open3.capture3(run_env, 'bash', 'hooks/pre-push', :chdir => repo)
      raise "pre-push runtime failed exit=#{status.exitstatus}: #{out}#{err}" unless status.success?
      raise 'pre-push returned success without executing acceptance entrypoint' unless File.file?(marker) && File.read(marker) == 'executed'
    end
    true
  end

  def wiring_check(root)
    workflow, text = yaml(File.join(root, WORKFLOW))
    raise 'pull_request_target is forbidden' if text.match?(/^\s*pull_request_target\s*:/)
    jobs = workflow['jobs']
    raise 'workflow jobs mapping missing' unless jobs.is_a?(Hash)
    job = jobs[REQUIRED_CHECK]
    raise "required job #{REQUIRED_CHECK} missing" unless job.is_a?(Hash)
    steps = job['steps']
    raise 'workflow steps missing' unless steps.is_a?(Array)
    candidates = steps.select do |step|
      next false unless step.is_a?(Hash) && step.key?('run')
      lines = executable_lines(step['run'])
      lines.length >= 1 && direct_acceptance_line?(lines.first)
    end
    raise "CI must directly execute #{ACCEPTANCE} exactly once" unless candidates.length == 1
    step = candidates.first
    raise 'CI verification step must not be conditional' if step.key?('if')
    raise 'CI verification step must not ignore errors' if step['continue-on-error'] == true
    raise 'CI verification step must produce a target-SHA report' unless step['run'].include?('--output') && step['run'].include?('GITHUB_SHA')
    upload = steps.any? do |candidate|
      with = candidate['with'] if candidate.is_a?(Hash)
      candidate.is_a?(Hash) && candidate['uses'].to_s.start_with?('actions/upload-artifact@') && with.is_a?(Hash) &&
        with['name'].to_s.include?('${{ github.sha }}') && with['path'].to_s.include?('${{ github.sha }}') &&
        with['if-no-files-found'] == 'error'
    end
    raise 'target-SHA verification result artifact upload missing' unless upload
    prepush_runtime_wiring(root)
    puts 'WIRING: ci_direct=1 pre_push_runtime=1 artifact=1'
    true
  end

  def policy_state(evidence)
    required = %w[
      repository workflow_identity required_check target_sha check_sha run_identity
      check_status check_conclusion target_kind pr_head_sha source protected_surface_changed
      separate_approval
    ]
    return 'FAIL' unless required.all? { |key| evidence.key?(key) && evidence[key] != nil && evidence[key] != '' }
    return 'UNVERIFIED' unless evidence['check_status'] == 'completed'
    return 'FAIL' unless evidence['check_conclusion'] == 'success'
    return 'FAIL' unless evidence['required_check'] == REQUIRED_CHECK
    return 'FAIL' unless evidence['workflow_identity'] == WORKFLOW_IDENTITY
    return 'FAIL' unless evidence['source'] == 'github_actions_api'
    case evidence['target_kind']
    when 'pr_head'
      return 'STALE' unless evidence['target_sha'] == evidence['pr_head_sha'] && evidence['check_sha'] == evidence['pr_head_sha']
    when 'merge_group'
      relation = evidence['merge_group_sha'] && evidence['merge_group_pr_head_sha']
      return 'FAIL' unless relation
      return 'FAIL' unless evidence['target_sha'] == evidence['merge_group_sha'] && evidence['check_sha'] == evidence['merge_group_sha']
      return 'FAIL' unless evidence['merge_group_pr_head_sha'] == evidence['pr_head_sha']
    else
      return 'FAIL'
    end
    return 'POLICY_REVIEW_REQUIRED' if evidence['protected_surface_changed'] == true || evidence['separate_approval'] != true
    'LOCAL_CANDIDATE'
  end

  def sha_one(path)
    data, _text = yaml(path)
    expected = data.delete('expected_state')
    actual = policy_state(data)
    puts "SHA_CASE: #{File.basename(path)} expected=#{expected} actual=#{actual}"
    raise "SHA fixture mismatch #{path}" unless actual == expected
    actual
  end

  def sha_fixtures(root)
    paths = Dir.glob(File.join(root, 'scripts/verify/fixtures/verification-authority/sha/*.yaml')).sort
    raise 'SHA fixtures missing' if paths.empty?
    states = paths.map { |path| sha_one(path) }
    required_states = %w[LOCAL_CANDIDATE STALE FAIL UNVERIFIED POLICY_REVIEW_REQUIRED]
    missing = required_states - states.uniq
    raise "SHA fixture state coverage missing #{missing.join(',')}" unless missing.empty?
    puts "SHA_FIXTURES: total=#{paths.length} states=#{states.uniq.sort.join(',')}"
    true
  end

  def working_tree_paths(root)
    status_out, _err, status = command(%w[git status --porcelain=v1], root)
    return [] unless status && status.success?
    status_out.lines.map { |line| line[3..-1].to_s.strip }.reject(&:empty?).uniq
  end
  def changed_paths(root)
    current = working_tree_paths(root)
    diff_out, _diff_err, diff_status = command(%w[git diff --name-only origin/main...HEAD], root)
    committed = diff_status && diff_status.success? ? diff_out.lines.map(&:strip) : []
    (current + committed).reject(&:empty?).uniq
  end

  def build_report(root, mutation_summary)
    contract = load_contract(root)
    sha_out, _sha_err, sha_status = command(%w[git rev-parse HEAD], root)
    head_sha = sha_status && sha_status.success? ? sha_out.strip : 'UNKNOWN'
    uncommitted = !working_tree_paths(root).empty? && ENV['GITHUB_SHA'].to_s.empty?
    target_sha = ENV['GITHUB_SHA'].to_s.empty? ? (uncommitted ? "UNCOMMITTED@#{head_sha}" : head_sha) : ENV['GITHUB_SHA']
    protected_changed = !(changed_paths(root) & INTRINSIC_PROTECTED).empty?
    status = protected_changed ? 'POLICY_REVIEW_REQUIRED' : 'LOCAL_CANDIDATE'
    {
      'status' => status,
      'repository' => 'sangmokang/Valuehire_v6',
      'workflow_identity' => WORKFLOW_IDENTITY,
      'required_check' => REQUIRED_CHECK,
      'target_sha' => target_sha,
      'run_identity' => ENV['GITHUB_RUN_ID'].to_s.empty? ? "local-#{Process.pid}" : ENV['GITHUB_RUN_ID'],
      'protected_surface_changed' => protected_changed,
      'unregistered_count' => contract['unregistered_requirements'].length,
      'unregistered_requirements' => contract['unregistered_requirements'],
      'mutation_total' => mutation_summary['total'],
      'mutation_blocked' => mutation_summary['blocked'],
      'mutation_survived' => mutation_summary['survived'],
      'normal_controls' => mutation_summary['controls'],
      'mutation_execution' => mutation_summary['execution'],
      'official_verified' => false,
      'remote_verification' => 'BLOCKED: new commit SHA is not on remote; no trusted GitHub Actions result'
    }
  end

  def write_report(path, report)
    FileUtils.mkdir_p(File.dirname(path))
    tmp = "#{path}.tmp"
    File.write(tmp, JSON.pretty_generate(report) + "\n")
    File.rename(tmp, path)
  end

  def derived_state_check(root)
    Dir.mktmpdir('verification-derived-') do |tmp|
      path = File.join(tmp, 'result.json')
      summary = { 'total' => 23, 'blocked' => 22, 'survived' => 0, 'controls' => 1,
                  'execution' => 'EXECUTED' }
      report = build_report(root, summary)
      write_report(path, report)
      tampered = JSON.parse(File.read(path))
      tampered['status'] = 'VERIFIED'
      tampered['target_sha'] = 'hand-edited'
      File.write(path, JSON.pretty_generate(tampered))
      write_report(path, build_report(root, summary))
      regenerated = JSON.parse(File.read(path))
      raise 'generated state tamper survived rerun' if regenerated['status'] == 'VERIFIED' || regenerated['target_sha'] == 'hand-edited'
      required = %w[status target_sha workflow_identity required_check unregistered_count mutation_survived]
      missing = required.reject { |key| regenerated.key?(key) }
      raise "derived report missing #{missing.join(',')}" unless missing.empty?
    end
    puts 'DERIVED_STATE: tamper_overwritten=1 required_fields=6'
    true
  end

  def authority_check(root)
    protected_check(root)
    forged = {
      'repository' => 'sangmokang/Valuehire_v6', 'workflow_identity' => WORKFLOW_IDENTITY,
      'required_check' => REQUIRED_CHECK, 'target_sha' => 'a' * 40, 'check_sha' => 'a' * 40,
      'run_identity' => 'llm-report', 'check_status' => 'completed', 'check_conclusion' => 'success',
      'target_kind' => 'pr_head', 'pr_head_sha' => 'a' * 40, 'source' => 'llm_report',
      'protected_surface_changed' => false, 'separate_approval' => true
    }
    state = policy_state(forged)
    raise 'LLM report created authority' unless state == 'FAIL'
    source = File.read(__FILE__)
    policy_source = source[/  def policy_state.*?(?=\n  def sha_one)/m]
    raise 'candidate policy contains official-state token' if policy_source.to_s.match?(/['\"]VERIFIED['\"]/)
    puts 'AUTHORITY: llm_report=FAIL candidate_policy_official_token=0 protected=DETECT_ONLY'
    true
  end

  def verify_all(root, include_mutations, output_path)
    captured = String.new
    begin
      raise '--no-mutations cannot generate evidence output' if !include_mutations && output_path
      contract = load_contract(root)
      contract['requirements'].each do |entry|
        next if !include_mutations && entry['id'] == 'VA-004'
        out, err, status = command(entry['verifier'], root)
        rc = status ? status.exitstatus : 255
        captured << "$ #{entry['verifier']}\n#{out}#{err}EXIT=#{rc}\n"
        raise "required verifier #{entry['id']} failed exit=#{rc}" unless status && status.success?
        marker = VERIFIER_MARKERS.fetch(entry['id'])
        raise "required verifier #{entry['id']} output marker missing" unless out.lines.any? { |line| line.start_with?(marker) }
      end
      mutation_summary = if include_mutations
                           mutation_summary_from(captured).merge('execution' => 'EXECUTED')
                         else
                           { 'total' => 0, 'blocked' => 0, 'survived' => 0, 'controls' => 0,
                             'execution' => 'SKIPPED_INTERNAL_CONTROL' }
                         end
      report = build_report(root, mutation_summary)
      raise 'local verifier must not emit VERIFIED' if report['status'] == 'VERIFIED'
      write_report(output_path, report) if output_path
      puts captured
      puts "AUTHORITY_RESULT: #{report['status']}"
      puts "TARGET_SHA: #{report['target_sha']}"
      puts "WORKFLOW_IDENTITY: #{report['workflow_identity']}"
      puts "REQUIRED_CHECK: #{report['required_check']}"
      puts "UNREGISTERED: #{report['unregistered_count']}"
      puts "MUTATION_SURVIVED: #{report['mutation_survived']}"
      puts "REPORT: #{output_path}" if output_path
      true
    rescue StandardError => e
      puts captured
      warn "VERIFIER_FAIL: #{e.message}"
      false
    end
  end
end

root = VerificationAuthority.repo_root
mode = ARGV.shift || 'verify-all'

begin
  ok = case mode
       when 'contract-self-test'
         VerificationAuthority.contract_self_test(root)
       when 'contract-execute'
         VerificationAuthority.contract_check(root, true, false)
         true
       when 'mutation-catalog-check'
         VerificationAuthority.mutation_catalog_check(root)
       when 'protected-check'
         VerificationAuthority.protected_check(root)
       when 'wiring-check'
         VerificationAuthority.wiring_check(root)
       when 'authority-check'
         VerificationAuthority.authority_check(root)
       when 'sha-one'
         path = ARGV.shift || raise('sha-one fixture path required')
         VerificationAuthority.sha_one(File.expand_path(path, root))
         true
       when 'sha-fixtures'
         VerificationAuthority.sha_fixtures(root)
       when 'recovery-one'
         name = ARGV.shift || raise('recovery-one name required')
         mapping = {
           'permission_restore_failure' => [%w[permission_restore_failure], 'PERMISSION_RESTORE_FAILED', true],
           'delete_attempt' => [%w[second_target_failure delete_attempt], 'DELETE_REFUSED', true]
         }
         args = mapping[name] || raise("unknown recovery-one #{name}")
         actual, present = VerificationAuthority.recovery_case(args[0], args[1], args[2])
         puts "RECOVERY_ONE: #{name} status=#{actual} state_present=#{present}"
         true
       when 'recovery-fixtures'
         VerificationAuthority.recovery_fixtures(root)
       when 'derived-state-check'
         VerificationAuthority.derived_state_check(root)
       when 'mutations'
         VerificationAuthority.mutations(root)
       when 'structural-limit-check'
         VerificationAuthority.structural_limit_check(root)
       when 'verify-all'
         include_mutations = !ARGV.delete('--no-mutations')
         output_index = ARGV.index('--output')
         output_path = output_index ? File.expand_path(ARGV[output_index + 1], root) : nil
         VerificationAuthority.verify_all(root, include_mutations, output_path)
       else
         raise "unknown mode #{mode}"
       end
  exit(ok ? 0 : 1)
rescue StandardError => e
  warn "VERIFIER_FAIL: #{e.message}"
  exit 1
end
