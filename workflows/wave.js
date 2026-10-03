export const meta = {
  name: 'spec-wave',
  description: 'Implement one spec wave: a spec-implementer per task, parallel within file-disjoint groups, in isolated worktrees',
  phases: [{ title: 'Implement', detail: 'one implementer per task; groups run in order, tasks in a group run in parallel' }],
}

// args (built by the orchestrator from spec-state):
// { spec, wave, groups: [[taskId]], sequential: [taskId],
//   tasks: { [id]: { block, files: [], wireInto } },   // block = the task's section of tasks.md
//   summary, manifest, lessons, fullSpec }               // strings; fullSpec may be ""

const RESULT = {
  type: 'object',
  properties: {
    task: { type: 'string' },
    failed: { type: 'boolean', description: 'true if the task could not be completed' },
    committed: { type: 'boolean', description: 'true if `git commit` succeeded in your checkout' },
    branch: { type: 'string', description: 'output of `git branch --show-current`' },
    worktree: { type: 'string', description: 'output of `git rev-parse --show-toplevel`' },
    files_changed: { type: 'array', items: { type: 'string' } },
    tests_run: { type: 'string', description: 'test command and its summary line' },
    wiring_evidence: { type: 'string', description: 'grep command and output that shows the import chain, or why n/a' },
    out_of_scope: { type: 'array', items: { type: 'string' }, description: 'OUT-OF-SCOPE / SIGNATURE BREAK notes for the orchestrator' },
    notes: { type: 'string' },
  },
  required: ['task', 'failed', 'committed', 'files_changed'],
}

function implPrompt(id, isParallel) {
  const t = args.tasks[id]
  return [
    `# Spec ${args.spec}, wave ${args.wave}: implement ${id}`,
    '', '## State summary', args.summary,
    '', '## Your task (the only one you implement)', t.block,
    '', '## File boundaries',
    `You MUST only create or modify these files: ${t.files.join(', ')}.`,
    isParallel
      ? 'Other implementers are working in parallel on other files. Do NOT touch any other file, do NOT run formatters, do NOT change existing function signatures (add-only). Record anything you needed outside your boundary in out_of_scope.'
      : 'You run alone; you may touch other files if the task genuinely needs it, but list every such file in out_of_scope.',
    `Wire into: ${t.wireInto || 'n/a'}`,
    '', '## Import manifest (use EXACTLY these names and paths)', args.manifest || '(no completed tasks yet)',
    args.lessons ? `\n## Lessons from past specs\n${args.lessons}` : '',
    args.fullSpec ? `\n## Full spec context\n${args.fullSpec}` : '',
    '', '## When done',
    '1. Run the tests you wrote and paste the summary line in tests_run.',
    '2. Grep for the import chain from the app entry point to your code; paste it in wiring_evidence.',
    `3. Commit in your current checkout: git add ${t.files.join(' ')} && git commit -m "feat: ${id}".`,
    '4. Report branch (`git branch --show-current`) and worktree (`git rev-parse --show-toplevel`).',
    'Do NOT edit .claude/specs/*/state.json or the Status/Wired lines in tasks.md; the orchestrator records them.',
  ].join('\n')
}

function implOpts(id, isParallel) {
  const o = { label: `impl:${id}`, phase: 'Implement', agentType: 'spec-engine:spec-implementer', schema: RESULT }
  if (isParallel) o.isolation = 'worktree'
  return o
}

const results = []
for (const group of args.groups) {
  // groups conflict on files with each other, so this barrier between groups is required
  const r = await parallel(group.map(id => () => agent(implPrompt(id, group.length > 1), implOpts(id, group.length > 1))))
  const got = r.filter(Boolean)
  const lost = group.filter(id => !got.some(x => x.task === id))
  if (lost.length) log(`implementers returned nothing for: ${lost.join(', ')}`)
  results.push(...got, ...lost.map(id => ({ task: id, failed: true, committed: false, files_changed: [], notes: 'agent returned no result' })))
  log(`group done: ${group.join(', ')}`)
}
for (const id of args.sequential || []) {
  const r = await agent(implPrompt(id, false), implOpts(id, false))
  results.push(r || { task: id, failed: true, committed: false, files_changed: [], notes: 'agent returned no result' })
}
return results
