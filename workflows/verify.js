export const meta = {
  name: 'spec-verify',
  description: 'Team mode: an independent spec-tester per implemented task, then one spec-reviewer over the whole wave',
  phases: [{ title: 'Test', detail: 'one tester per task, in parallel' }, { title: 'Review', detail: 'one Opus reviewer for the wave' }],
}

// args: { spec, wave, tasks: { [id]: { block, handoff } }, ids: [taskId], diff, wiringEvidence, design, team: boolean }

const TEST = {
  type: 'object',
  properties: {
    task: { type: 'string' },
    verdict: { type: 'string', enum: ['VERIFIED', 'WIRING_FAIL', 'FUNCTIONAL_FAIL'] },
    evidence: { type: 'string', description: 'commands run and their output summaries' },
    failures: { type: 'array', items: { type: 'string' } },
    test_files: { type: 'array', items: { type: 'string' } },
  },
  required: ['task', 'verdict', 'evidence'],
}

const REVIEW = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['APPROVED', 'REJECTED'] },
    report: { type: 'string', description: 'full markdown report in the spec-reviewer format' },
    critical: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, file: { type: 'string' }, fix: { type: 'string' } }, required: ['title', 'file', 'fix'] } },
    counts: { type: 'object', properties: { critical: { type: 'integer' }, high: { type: 'integer' }, medium: { type: 'integer' } }, required: ['critical', 'high', 'medium'] },
    rejected_tasks: { type: 'array', items: { type: 'string' } },
    human_review: { type: 'string' },
  },
  required: ['verdict', 'report', 'critical', 'counts', 'rejected_tasks'],
}

let tests = []
if (args.team) {
  tests = (await parallel(args.ids.map(id => () => agent([
    `# Spec ${args.spec}, wave ${args.wave}: verify ${id}`,
    '## Task', args.tasks[id].block,
    '## Implementer handoff', args.tasks[id].handoff || '(none)',
    '## Wiring evidence from spec-state', args.wiringEvidence,
    'Follow your Step 0 (independent wiring check) then functional and error-path testing. Return the structured result.',
  ].join('\n\n'), { label: `test:${id}`, phase: 'Test', agentType: 'spec-engine:spec-tester', schema: TEST })))).filter(Boolean)
  log(`tests: ${tests.filter(t => t.verdict === 'VERIFIED').length}/${args.ids.length} verified`)
}

const review = await agent([
  `# Spec ${args.spec}, wave ${args.wave}: review`,
  '## Tasks in this wave', args.ids.map(id => args.tasks[id].block).join('\n\n'),
  '## Wiring evidence', args.wiringEvidence,
  tests.length ? `## Tester results\n${JSON.stringify(tests, null, 2)}` : '',
  '## design.md', args.design,
  '## Diff for the wave', args.diff,
  'Run the full checklist (wiring, security, quality, architecture, cross-task). Return the structured result; `report` must be the complete markdown report.',
].join('\n\n'), { label: `review:wave-${args.wave}`, phase: 'Review', agentType: 'spec-engine:spec-reviewer', schema: REVIEW })

return { tests, review }
